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

## 🧠 Kernel-Space Bridge

- `kernel/linux_kernel_bridge.c` is the kernel-space companion to the user-space Python bridge.
- It exposes a `/dev/linux_kernel_bridge` character device and `/proc/linux_kernel_bridge` status output.
- The module supports `read`, `write`, `llseek`, and `ioctl` so user space can talk to it through a normal file descriptor.
- Build it from `kernel/` with `make`, then load it with `sudo insmod linux_kernel_bridge.ko`.

## ⚛️ React Frontend

- The front end still has the live single-file shell at `frontend/react_app.html`.
- The JSX source extracted from that shell now lives in `frontend/src/App.jsx` and `frontend/src/main.jsx`.
- The old standalone HTML pages have been removed from the repo.
- Legacy `.html` routes still work because Flask routes them into the same shell.
- The existing audio, image, video, and PDF assets stay in `frontend/assets/` so the React source can keep using them.

## 🧩 Modular Flask Backend

- The new Flask package lives under `backend/app/` with `routes/`, `services/`, `models/`, `schemas/`, `utils/`, and `middleware/`.
- Launch the modular entrypoint with `python3 backend/run.py` or `python3 -m backend.run`.
- The modular app attaches to the existing Flask instance, so the legacy routes and the new organized API routes share the same SQLite database and session state.
- New organized API prefixes are available for `auth`, `users`, `tracks`, and `uploads` under `/api/auth`, `/api/users`, `/api/tracks`, and `/api/uploads`.

## 📌 Status

This project is currently under development and new features are continuously being added.
# render
