<?php
require "config.php";
header("Content-Type: application/json");

$data = json_decode(file_get_contents("php://input"), true);

if (!isset($data["email"], $data["password"])) {
  http_response_code(400);
  echo json_encode(["message" => "INVALID INPUT"]);
  exit;
}

$email = strtolower(trim($data["email"]));
$password = $data["password"];

/* get user */
[$status, $users] = supabase_request(
  "GET",
  "users?email=eq.$email&select=id,username,password"
);

if (empty($users) || !password_verify($password, $users[0]["password"])) {
  http_response_code(401);
  echo json_encode(["message" => "INVALID CREDENTIALS"]);
  exit;
}

session_start();
$_SESSION["user_id"] = $users[0]["id"];
$_SESSION["username"] = $users[0]["username"];

echo json_encode([
  "message" => "ACCESS GRANTED",
  "username" => $users[0]["username"]
]);
