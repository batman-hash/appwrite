# CyberGhost Web App - Docker Setup

This directory contains Docker configuration files for running the CyberGhost Web Application.

## Quick Start

### Prerequisites

- Docker installed on your system
- Docker Compose (optional, but recommended)
- `.env` file in the parent directory with required environment variables

### Running with Docker Compose (Recommended)

```bash
# From the render/docker directory
./run_docker.sh run
```

Or manually:

```bash
docker-compose up -d
```

### Running with Docker Run

```bash
# From the render/docker directory
./run_docker.sh run-docker
```

Or manually:

```bash
# Build the image
docker build -t cyberghost-webapp -f docker/Dockerfile .

# Run the container
docker run -d \
  --name cyberghost-webapp \
  -p 8011:8011 \
  -v ../frontend:/app/frontend \
  -v ../certs:/app/certs:ro \
  -v ./data:/app/data \
  -v ./logs:/app/logs \
  --env-file ../.env \
  -e HOST=0.0.0.0 \
  -e PORT=8011 \
  cyberghost-webapp
```

## Available Commands

The `run_docker.sh` script provides the following commands:

| Command | Description |
|---------|-------------|
| `build` | Build the Docker image |
| `run` | Run with docker-compose (builds if needed) |
| `run-docker` | Run with docker run (builds if needed) |
| `start` | Start the container |
| `stop` | Stop the container |
| `restart` | Restart the container |
| `logs` | Show container logs |
| `status` | Show container status |
| `cleanup` | Stop and remove container |
| `help` | Show help message |

### Examples

```bash
# Build the image
./run_docker.sh build

# Run the application
./run_docker.sh run

# View logs
./run_docker.sh logs

# Stop the application
./run_docker.sh stop

# Check status
./run_docker.sh status
```

## Configuration

### Environment Variables

The application uses environment variables from the `.env` file in the parent directory. Key variables include:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host to bind to |
| `PORT` | `8011` | Port to listen on |
| `DEBUG` | `false` | Enable debug mode |
| `SECRET_KEY` | - | Flask secret key |
| `CORS_ORIGINS` | `http://localhost:8011,http://127.0.0.1:8011` | Allowed CORS origins |

### SSL Certificates

If you place certificate files in `../certs/` with these names:

- `server.crt`
- `server.key`

the Docker entrypoint will start Gunicorn with HTTPS automatically. The Compose file mounts that folder as read-only at `/app/certs`.

### Volumes

The following volumes are mounted:

| Host Path | Container Path | Description |
|-----------|----------------|-------------|
| `../frontend` | `/app/frontend` | Frontend static files |
| `../certs` | `/app/certs` | HTTPS certificates, mounted read-only |
| `./data` | `/app/data` | Application data |
| `./logs` | `/app/logs` | Log files |

## API Endpoints

The application provides the following API endpoints:

### Health Check
- `GET /api/health` - Health check endpoint

### Network Operations
- `GET /api/network/info` - Get network information
- `POST /api/network/scan` - Scan network for devices
- `POST /api/network/scan-ports` - Scan ports on a target
- `POST /api/network/monitor` - Monitor network connection
- `POST /api/network/dns/setup` - Setup DNS configuration
- `POST /api/network/connection/test` - Test connection stability

### Firewall
- `POST /api/firewall/setup` - Setup firewall rules

### Devices
- `POST /api/devices/save` - Save discovered devices
- `POST /api/devices/load` - Load devices from file

## Troubleshooting

### Container won't start

1. Check if port 8011 is already in use:
   ```bash
   lsof -i :8011
   ```

2. Check container logs:
   ```bash
   ./run_docker.sh logs
   ```

3. Verify `.env` file exists and has correct values

### Permission issues

If you encounter permission issues with mounted volumes:

```bash
sudo chown -R $USER:$USER data logs
```

### Health check failing

The container includes a health check that runs every 30 seconds. If the health check fails:

1. Check if the application is running:
   ```bash
   docker ps
   ```

2. View application logs:
   ```bash
   docker logs cyberghost-webapp
   ```

3. Verify the application is responding:
   ```bash
   curl http://localhost:8011/api/health
   ```

## Development

### Building for development

For development, you may want to run with debug mode:

```bash
# Set DEBUG=true in .env file
DEBUG=true ./run_docker.sh run
```

### Rebuilding after changes

If you make changes to the code:

```bash
./run_docker.sh cleanup
./run_docker.sh build
./run_docker.sh run
```

## Production Deployment

For production deployment:

1. Ensure `DEBUG=false` in `.env`
2. Set a strong `SECRET_KEY`
3. Configure proper `CORS_ORIGINS`
4. Use a reverse proxy (nginx) for SSL termination
5. Consider using Docker Swarm or Kubernetes for orchestration

## Files

- `Dockerfile` - Docker image configuration
- `docker-compose.yml` - Docker Compose configuration
- `run_docker.sh` - Helper script for common operations
- `README.md` - This documentation file

## Support

For issues or questions, please refer to the main project documentation or create an issue in the project repository.
