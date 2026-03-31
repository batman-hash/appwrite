<?php
header("Content-Type: application/json");

session_start();

/* destroy session */
$_SESSION = [];
session_destroy();

/* delete session cookie (important) */
if (ini_get("session.use_cookies")) {
  $params = session_get_cookie_params();
  setcookie(
    session_name(),
    '',
    time() - 42000,
    $params["path"],
    $params["domain"],
    $params["secure"],
    $params["httponly"]
  );
}

echo json_encode([
  "success" => true,
  "message" => "LOGGED OUT SUCCESSFULLY"
]);
