<?php
require "config.php";
header("Content-Type: application/json");

/* 1. Read input */
$data = json_decode(file_get_contents("php://input"), true);

if (!isset($data["email"], $data["username"], $data["password"])) {
  http_response_code(400);
  echo json_encode(["message" => "INVALID INPUT"]);
  exit;
}

/* 2. Normalize + hash */
$email = strtolower(trim($data["email"]));
$username = trim($data["username"]);
$password = password_hash($data["password"], PASSWORD_DEFAULT);

/* 3. Check if email exists (from first script) */
[$status, $existing] = supabase_request(
  "GET",
  "users?email=eq.$email&select=id"
);

if (!empty($existing)) {
  http_response_code(409);
  echo json_encode(["message" => "EMAIL ALREADY REGISTERED"]);
  exit;
}

/* 4. Insert user AND return row (from second script) */
[$status, $inserted] = supabase_request(
  "POST",
  "users?select=id,username,email",
  [
    "email" => $email,
    "username" => $username,
    "password" => $password
  ]
);

if ($status !== 201 || empty($inserted)) {
  http_response_code(500);
  echo json_encode(["message" => "REGISTRATION FAILED"]);
  exit;
}

/* 5. AUTO LOGIN (from second script) */
session_start();
$_SESSION["user_id"] = $inserted[0]["id"];
$_SESSION["username"] = $inserted[0]["username"];

sleep(1); // optional latency illusion

/* 6. Success response (from first + second) */
echo json_encode([
  "succ
