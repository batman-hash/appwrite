#include <iostream>

#include "email_sender.h"

int main() {
    std::cout << "DevNavigator starting...\n";

    process_and_send_emails("../database/devnav.db");

    return 0;
}
