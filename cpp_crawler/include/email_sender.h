#ifndef CPP_CRAWLER_EMAIL_SENDER_H
#define CPP_CRAWLER_EMAIL_SENDER_H

#include <string>

bool send_email(const std::string& to, const std::string& name);
void process_and_send_emails(const std::string& db_path);

#endif  // CPP_CRAWLER_EMAIL_SENDER_H
