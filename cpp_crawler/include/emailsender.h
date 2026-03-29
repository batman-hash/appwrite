#ifndef CPP_CRAWLER_EMAILSENDER_H
#define CPP_CRAWLER_EMAILSENDER_H

#include <string>
#include <vector>

struct EmailMessage {
  std::string recipient;
  std::string subject;
  std::string body;
};

class EmailSender {
 public:
  EmailSender(std::string smtp_server, int port);

  bool send(const EmailMessage& message) const;
  bool send_batch(const std::vector<EmailMessage>& messages) const;

 private:
  std::string smtp_server_;
  int port_;
};

#endif  // CPP_CRAWLER_EMAILSENDER_H
