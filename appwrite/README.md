# The-ghost-app

## 🎧 Digital Music Platform

A web platform designed for music producers and audio creators.  
The project provides a marketplace and community space where users can explore digital music tools and connect with other creators.

The platform includes sample packs, audio plugins, music production blogs, and interactive community features such as chat and user suggestions.

## 🚀 Features

- 🎵 Digital music sample packs
- 🔌 Audio plugins for music production
- 📝 Music production blogs and tutorials
- 💬 Community chat for producers
- 💡 User suggestions and feedback system
- 🛒 Online shop for digital music products

## 🌐 Purpose

The goal of this project is to create a central hub where music creators can discover tools, learn production techniques, and interact with a creative community.

## 🛠️ Technologies

- HTML / CSS / JavaScript  
- Git & GitHub for version control  
- Web technologies for building an interactive platform

## 🔒 Secure Socket Transfer

- `backend/secure_transfer.py` adds a native TLS socket path for client/server byte transfer.
- It sends data in chunks with ACK/NACK retries and SHA-256 verification so the client only accepts matching bytes.
- Server TLS keys stay on the server. If you want mutual TLS, give the client its own cert/key pair and keep that private key on the client side.
- `probe-loss` uses Scapy when available and falls back to `ping` so you can inspect link loss before transfer.

## ⚛️ React Frontend

- The front end is now served from a single React entry at `frontend/react_app.html`.
- Legacy `.html` routes still work, but Flask now routes them into that one shell.
- The existing audio, image, video, and PDF assets stay in `frontend/assets/` so the React page can keep using them.

## 📌 Status

This project is currently under development and new features are continuously being added.
# render
