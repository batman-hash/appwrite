<?php
define("SUPABASE_URL", "https://xxxx.supabase.co");
define("SUPABASE_KEY", "ANON_PUBLIC_KEY");

function supabase_request($method, $endpoint, $data = null) {
  $ch = curl_init(SUPABASE_URL . "/rest/v1/" . $endpoint);

  $headers = [
    "apikey: " . SUPABASE_KEY,
    "Authorization: Bearer " . SUPABASE_KEY,
    "Content-Type: application/json",
    "Prefer: return=minimal"
  ];

  curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_CUSTOMREQUEST => $method,
    CURLOPT_HTTPHEADER => $headers
  ]);

  if ($data) {
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
  }

  $response = curl_exec($ch);
  $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
  curl_close($ch);

  return [$status, json_decode($response, true)];
}
