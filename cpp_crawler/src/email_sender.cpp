#include "email_sender.h"

#include <curl/curl.h>

#include <cstdlib>
#include <cstring>
#include <iostream>
#include <sstream>
#include <sqlite3.h>

namespace {

struct UploadStatus {
    const std::string* payload = nullptr;
    size_t bytes_read = 0;
};

const char* get_env_or_null(const char* key) {
    return std::getenv(key);
}

std::string get_env_or_default(const char* key, const std::string& fallback) {
    const char* value = get_env_or_null(key);
    return value != nullptr ? value : fallback;
}

bool env_flag_enabled(const char* key, bool default_value) {
    const char* value = get_env_or_null(key);

    if (value == nullptr) {
        return default_value;
    }

    return std::strcmp(value, "1") == 0 || std::strcmp(value, "true") == 0 ||
           std::strcmp(value, "TRUE") == 0 ||
           std::strcmp(value, "yes") == 0 || std::strcmp(value, "YES") == 0;
}

std::string read_sqlite_text(sqlite3_stmt* stmt, int column) {
    const unsigned char* text = sqlite3_column_text(stmt, column);
    return text != nullptr ? reinterpret_cast<const char*>(text) : "";
}

std::string build_email_body(const std::string& name) {
    std::ostringstream body;
    const std::string greeting_name = name.empty() ? "there" : name;

    body << "Hi " << greeting_name << ",\r\n\r\n"
         << "We are launching a commercial app project for children and "
         << "wanted to share it with you.\r\n\r\n"
         << "The app is designed to help children learn through a blog-style "
         << "experience with educational content about information, culture, "
         << "stories, religion, and interactive pop-up features.\r\n\r\n"
         << "If you would like to hear more about the project, reply to this "
         << "email and we will follow up with details.\r\n\r\n"
         << "Best regards,\r\n"
         << "DevNavigator\r\n";

    return body.str();
}

std::string build_email_payload(const std::string& from,
                                const std::string& to,
                                const std::string& subject,
                                const std::string& body) {
    std::ostringstream payload;
    payload << "To: <" << to << ">\r\n"
            << "From: <" << from << ">\r\n"
            << "Subject: " << subject << "\r\n"
            << "MIME-Version: 1.0\r\n"
            << "Content-Type: text/plain; charset=utf-8\r\n"
            << "\r\n"
            << body;
    return payload.str();
}

size_t payload_source(char* buffer,
                      size_t size,
                      size_t nmemb,
                      void* user_data) {
    UploadStatus* upload = static_cast<UploadStatus*>(user_data);
    const size_t buffer_size = size * nmemb;
    const size_t remaining = upload->payload->size() - upload->bytes_read;
    const size_t copy_size = remaining < buffer_size ? remaining : buffer_size;

    if (copy_size == 0) {
        return 0;
    }

    std::memcpy(buffer, upload->payload->data() + upload->bytes_read, copy_size);
    upload->bytes_read += copy_size;
    return copy_size;
}

}  // namespace

bool send_email(const std::string& to, const std::string& name) {
    const std::string smtp_url =
        get_env_or_default("SMTP_URL", "smtp://localhost:587");
    const std::string smtp_username = get_env_or_default("SMTP_USERNAME", "");
    const std::string smtp_password = get_env_or_default("SMTP_PASSWORD", "");
    const std::string smtp_from =
        get_env_or_default("SMTP_FROM", "devnavigator@example.com");
    const bool use_tls = env_flag_enabled("SMTP_USE_TLS", true);
    const bool verify_tls = !env_flag_enabled("SMTP_SKIP_TLS_VERIFY", false);
    const bool verbose = env_flag_enabled("SMTP_VERBOSE", false);

    const std::string subject = "We are launching a new children's learning app";
    const std::string body = build_email_body(name);
    const std::string payload =
        build_email_payload(smtp_from, to, subject, body);

    CURL* curl = curl_easy_init();
    if (curl == nullptr) {
        std::cerr << "Failed to initialize libcurl\n";
        return false;
    }

    UploadStatus upload{&payload, 0};
    struct curl_slist* recipients = nullptr;
    CURLcode result = CURLE_OK;

    recipients = curl_slist_append(recipients, ("<" + to + ">").c_str());

    curl_easy_setopt(curl, CURLOPT_URL, smtp_url.c_str());
    curl_easy_setopt(curl, CURLOPT_MAIL_FROM, ("<" + smtp_from + ">").c_str());
    curl_easy_setopt(curl, CURLOPT_MAIL_RCPT, recipients);
    curl_easy_setopt(curl, CURLOPT_READFUNCTION, payload_source);
    curl_easy_setopt(curl, CURLOPT_READDATA, &upload);
    curl_easy_setopt(curl, CURLOPT_UPLOAD, 1L);
    curl_easy_setopt(curl, CURLOPT_USE_SSL,
                     use_tls ? CURLUSESSL_ALL : CURLUSESSL_NONE);
    curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, verify_tls ? 1L : 0L);
    curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, verify_tls ? 2L : 0L);
    curl_easy_setopt(curl, CURLOPT_VERBOSE, verbose ? 1L : 0L);
    curl_easy_setopt(curl, CURLOPT_CONNECTTIMEOUT, 10L);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 30L);

    if (!smtp_username.empty()) {
        curl_easy_setopt(curl, CURLOPT_USERNAME, smtp_username.c_str());
    }

    if (!smtp_password.empty()) {
        curl_easy_setopt(curl, CURLOPT_PASSWORD, smtp_password.c_str());
    }

    result = curl_easy_perform(curl);

    if (result != CURLE_OK) {
        std::cerr << "SMTP send failed for " << to << ": "
                  << curl_easy_strerror(result) << "\n";
    } else {
        std::cout << "Sent email to: " << to << " (" << name << ")\n";
    }

    curl_slist_free_all(recipients);
    curl_easy_cleanup(curl);
    return result == CURLE_OK;
}

void process_and_send_emails(const std::string& db_path) {
    sqlite3* db = nullptr;
    sqlite3_stmt* stmt = nullptr;

    if (sqlite3_open(db_path.c_str(), &db) != SQLITE_OK) {
        std::cerr << "Failed to open DB at " << db_path;
        if (db != nullptr) {
            std::cerr << ": " << sqlite3_errmsg(db);
        }
        std::cerr << "\n";
        sqlite3_close(db);
        return;
    }

    if (curl_global_init(CURL_GLOBAL_DEFAULT) != CURLE_OK) {
        std::cerr << "Failed to initialize libcurl globals\n";
        sqlite3_close(db);
        return;
    }

    const char* select_sql =
        "SELECT id, email, name FROM contacts "
        "WHERE consent = 1 AND sent = 0 LIMIT 50;";

    if (sqlite3_prepare_v2(db, select_sql, -1, &stmt, nullptr) != SQLITE_OK) {
        std::cerr << "Query failed\n";
        curl_global_cleanup();
        sqlite3_close(db);
        return;
    }

    while (sqlite3_step(stmt) == SQLITE_ROW) {
        int id = sqlite3_column_int(stmt, 0);
        std::string email = read_sqlite_text(stmt, 1);
        std::string name = read_sqlite_text(stmt, 2);

        if (email.empty()) {
            std::cerr << "Skipping contact " << id << " due to missing email\n";
            continue;
        }

        if (send_email(email, name)) {
            sqlite3_stmt* update_stmt = nullptr;
            const char* update_sql =
                "UPDATE contacts SET sent = 1 WHERE id = ?;";

            if (sqlite3_prepare_v2(db, update_sql, -1, &update_stmt, nullptr) !=
                SQLITE_OK) {
                std::cerr << "Failed to prepare sent-status update for " << email
                          << "\n";
                continue;
            }

            sqlite3_bind_int(update_stmt, 1, id);
            if (sqlite3_step(update_stmt) != SQLITE_DONE) {
                std::cerr << "Failed to mark contact as sent: " << email << "\n";
            } else {
                std::cout << "Marked as sent: " << email << "\n";
            }
            sqlite3_finalize(update_stmt);
        }
    }

    sqlite3_finalize(stmt);
    curl_global_cleanup();
    sqlite3_close(db);
}
