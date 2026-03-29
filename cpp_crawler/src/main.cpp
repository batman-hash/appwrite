#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <vector>

#include "email_sender.h"

namespace {

std::filesystem::path first_existing_path(
    const std::vector<std::filesystem::path>& candidates) {
    for (const auto& candidate : candidates) {
        if (!candidate.empty() && std::filesystem::exists(candidate)) {
            return candidate;
        }
    }

    return {};
}

std::filesystem::path resolve_database_path(int argc, char* argv[]) {
    if (argc > 1 && argv[1] != nullptr && std::string(argv[1]).size() > 0) {
        return std::filesystem::path(argv[1]);
    }

    if (const char* env_db_path = std::getenv("DATABASE_PATH");
        env_db_path != nullptr && std::string(env_db_path).size() > 0) {
        return std::filesystem::path(env_db_path);
    }

    const auto cwd = std::filesystem::current_path();
    const auto exe_dir =
        std::filesystem::absolute(argv[0]).parent_path();

    const auto resolved = first_existing_path({
        cwd / "database" / "devnav.db",
        cwd / ".." / "database" / "devnav.db",
        cwd / ".." / ".." / "database" / "devnav.db",
        exe_dir / ".." / ".." / "database" / "devnav.db",
        exe_dir / ".." / ".." / ".." / "database" / "devnav.db",
    });

    if (!resolved.empty()) {
        return resolved.lexically_normal();
    }

    return (exe_dir / ".." / ".." / "database" / "devnav.db").lexically_normal();
}

}  // namespace

int main(int argc, char* argv[]) {
    const auto db_path = resolve_database_path(argc, argv);

    std::cout << "DevNavigator starting...\n";
    std::cout << "Using database: " << db_path << "\n";

    process_and_send_emails(db_path.string());

    return 0;
}
