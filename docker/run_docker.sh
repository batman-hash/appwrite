#!/bin/bash
# CyberGhost Web App - Docker Run Script
# This script builds and runs the CyberGhost web application using Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="cyberghost-webapp"
MAC_ROTATOR_NAME="cyberghost-mac-rotator"
IP_ROTATOR_NAME="cyberghost-ip-rotator"
FIREWALL_NAME="cyberghost-firewall"
IMAGE_NAME="cyberghost-webapp"
PORT=8011
CERTS_DIR="$(cd "$(dirname "$0")/.." && pwd)/certs"
if [ -f "$CERTS_DIR/server.crt" ] && [ -f "$CERTS_DIR/server.key" ]; then
    WEB_SCHEME="https"
else
    WEB_SCHEME="http"
fi

echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}  CyberGhost Web App - Docker Setup${NC}"
echo -e "${GREEN}==========================================${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Warning: docker-compose not found, trying 'docker compose'${NC}"
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Function to stop and remove existing container
cleanup() {
    echo -e "${YELLOW}Cleaning up existing containers...${NC}"
    docker stop $CONTAINER_NAME 2>/dev/null || true
    docker rm $CONTAINER_NAME 2>/dev/null || true
    docker stop $MAC_ROTATOR_NAME 2>/dev/null || true
    docker rm $MAC_ROTATOR_NAME 2>/dev/null || true
    docker stop $IP_ROTATOR_NAME 2>/dev/null || true
    docker rm $IP_ROTATOR_NAME 2>/dev/null || true
    docker stop $FIREWALL_NAME 2>/dev/null || true
    docker rm $FIREWALL_NAME 2>/dev/null || true
}

# Function to build the image
build() {
    echo -e "${GREEN}Building Docker image...${NC}"
    cd "$(dirname "$0")/.."
    docker build -t $IMAGE_NAME -f docker/Dockerfile .
    echo -e "${GREEN}Image built successfully!${NC}"
}

# Function to run with docker-compose
run_compose() {
    echo -e "${GREEN}Starting with docker-compose...${NC}"
    cd "$(dirname "$0")"
    $COMPOSE_CMD up -d
    echo -e "${GREEN}Containers started successfully!${NC}"
    echo -e "${GREEN}Web App: ${WEB_SCHEME}://localhost:$PORT${NC}"
    echo -e "${GREEN}MAC Rotator: Running every 60 seconds${NC}"
    echo -e "${GREEN}IP Rotator: Running every 60 seconds${NC}"
    echo -e "${GREEN}Firewall: Active (blocking sniffers, injection, file transfers)${NC}"
}

# Function to run with docker run
run_docker() {
    echo -e "${GREEN}Starting with docker run...${NC}"
    cleanup
    
    # Create necessary directories
    mkdir -p data logs
    
    # Run web app
    docker run -d \
        --name $CONTAINER_NAME \
        -p $PORT:$PORT \
        -v "$(pwd)/../frontend:/app/frontend" \
        -v "$(pwd)/../certs:/app/certs:ro" \
        -v "$(pwd)/data:/app/data" \
        -v "$(pwd)/logs:/app/logs" \
        --env-file ../.env \
        -e HOST=0.0.0.0 \
        -e PORT=$PORT \
        -e DEBUG=false \
        --restart unless-stopped \
        $IMAGE_NAME
    
    # Run MAC rotator
    docker run -d \
        --name $MAC_ROTATOR_NAME \
        -v "$(pwd)/logs:/app/logs" \
        --cap-add NET_ADMIN \
        --privileged \
        --restart unless-stopped \
        $IMAGE_NAME \
        python mac_rotation.py --interval 60
    
    # Run IP rotator
    docker run -d \
        --name $IP_ROTATOR_NAME \
        -v "$(pwd)/logs:/app/logs" \
        --cap-add NET_ADMIN \
        --privileged \
        --restart unless-stopped \
        $IMAGE_NAME \
        python ip_rotation.py --interval 60 --subnet 192.168.1.0/24
    
    # Run firewall
    docker run -d \
        --name $FIREWALL_NAME \
        -v "$(pwd)/logs:/app/logs" \
        --cap-add NET_ADMIN \
        --privileged \
        --restart unless-stopped \
        $IMAGE_NAME \
        python firewall_setup.py --apply --allow-web
    
    echo -e "${GREEN}Containers started successfully!${NC}"
    echo -e "${GREEN}Web App: ${WEB_SCHEME}://localhost:$PORT${NC}"
    echo -e "${GREEN}MAC Rotator: Running every 60 seconds${NC}"
    echo -e "${GREEN}IP Rotator: Running every 60 seconds${NC}"
    echo -e "${GREEN}Firewall: Active (blocking sniffers, injection, file transfers)${NC}"
}

# Function to run only web app (no MAC/IP rotation, no firewall)
run_web_only() {
    echo -e "${GREEN}Starting web app only (no MAC/IP rotation, no firewall)...${NC}"
    cleanup
    
    # Create necessary directories
    mkdir -p data logs
    
    docker run -d \
        --name $CONTAINER_NAME \
        -p $PORT:$PORT \
        -v "$(pwd)/../frontend:/app/frontend" \
        -v "$(pwd)/../certs:/app/certs:ro" \
        -v "$(pwd)/data:/app/data" \
        -v "$(pwd)/logs:/app/logs" \
        --env-file ../.env \
        -e HOST=0.0.0.0 \
        -e PORT=$PORT \
        -e DEBUG=false \
        --restart unless-stopped \
        $IMAGE_NAME
    
    echo -e "${GREEN}Web app started successfully!${NC}"
    echo -e "${GREEN}Access the application at: ${WEB_SCHEME}://localhost:$PORT${NC}"
}

# Function to run only MAC rotator
run_mac_only() {
    echo -e "${GREEN}Starting MAC rotator only...${NC}"
    docker stop $MAC_ROTATOR_NAME 2>/dev/null || true
    docker rm $MAC_ROTATOR_NAME 2>/dev/null || true
    
    # Create necessary directories
    mkdir -p logs
    
    docker run -d \
        --name $MAC_ROTATOR_NAME \
        -v "$(pwd)/logs:/app/logs" \
        --cap-add NET_ADMIN \
        --privileged \
        --restart unless-stopped \
        $IMAGE_NAME \
        python mac_rotation.py --interval 60
    
    echo -e "${GREEN}MAC rotator started successfully!${NC}"
    echo -e "${GREEN}Rotating MAC addresses every 60 seconds${NC}"
}

# Function to run only IP rotator
run_ip_only() {
    echo -e "${GREEN}Starting IP rotator only...${NC}"
    docker stop $IP_ROTATOR_NAME 2>/dev/null || true
    docker rm $IP_ROTATOR_NAME 2>/dev/null || true
    
    # Create necessary directories
    mkdir -p logs
    
    docker run -d \
        --name $IP_ROTATOR_NAME \
        -v "$(pwd)/logs:/app/logs" \
        --cap-add NET_ADMIN \
        --privileged \
        --restart unless-stopped \
        $IMAGE_NAME \
        python ip_rotation.py --interval 60 --subnet 192.168.1.0/24
    
    echo -e "${GREEN}IP rotator started successfully!${NC}"
    echo -e "${GREEN}Rotating IP addresses every 60 seconds${NC}"
}

# Function to run only firewall
run_firewall_only() {
    echo -e "${GREEN}Starting firewall only...${NC}"
    docker stop $FIREWALL_NAME 2>/dev/null || true
    docker rm $FIREWALL_NAME 2>/dev/null || true
    
    # Create necessary directories
    mkdir -p logs
    
    docker run -d \
        --name $FIREWALL_NAME \
        -v "$(pwd)/logs:/app/logs" \
        --cap-add NET_ADMIN \
        --privileged \
        --restart unless-stopped \
        $IMAGE_NAME \
        python firewall_setup.py --apply --allow-web
    
    echo -e "${GREEN}Firewall started successfully!${NC}"
    echo -e "${GREEN}Blocking sniffers, injection attacks, file transfers${NC}"
}

# Function to show logs
show_logs() {
    echo -e "${GREEN}Showing container logs...${NC}"
    docker logs -f $CONTAINER_NAME
}

# Function to show MAC rotator logs
show_mac_logs() {
    echo -e "${GREEN}Showing MAC rotator logs...${NC}"
    docker logs -f $MAC_ROTATOR_NAME
}

# Function to show IP rotator logs
show_ip_logs() {
    echo -e "${GREEN}Showing IP rotator logs...${NC}"
    docker logs -f $IP_ROTATOR_NAME
}

# Function to show firewall logs
show_firewall_logs() {
    echo -e "${GREEN}Showing firewall logs...${NC}"
    docker logs -f $FIREWALL_NAME
}

# Function to stop the container
stop() {
    echo -e "${YELLOW}Stopping containers...${NC}"
    docker stop $CONTAINER_NAME 2>/dev/null || true
    docker stop $MAC_ROTATOR_NAME 2>/dev/null || true
    docker stop $IP_ROTATOR_NAME 2>/dev/null || true
    docker stop $FIREWALL_NAME 2>/dev/null || true
    echo -e "${GREEN}Containers stopped!${NC}"
}

# Function to show status
status() {
    echo -e "${GREEN}Container status:${NC}"
    docker ps -a | grep -E "$CONTAINER_NAME|$MAC_ROTATOR_NAME|$IP_ROTATOR_NAME|$FIREWALL_NAME" || echo -e "${YELLOW}No containers found${NC}"
}

# Function to show help
show_help() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build           - Build the Docker image"
    echo "  run             - Run with docker-compose (web + MAC + IP + firewall)"
    echo "  run-docker      - Run with docker run (web + MAC + IP + firewall)"
    echo "  run-web         - Run web app only (no MAC/IP rotation, no firewall)"
    echo "  run-mac         - Run MAC rotator only"
    echo "  run-ip          - Run IP rotator only"
    echo "  run-firewall    - Run firewall only"
    echo "  start           - Start with docker-compose"
    echo "  stop            - Stop all containers"
    echo "  restart         - Restart all containers"
    echo "  logs            - Show web app logs"
    echo "  mac-logs        - Show MAC rotator logs"
    echo "  ip-logs         - Show IP rotator logs"
    echo "  firewall-logs   - Show firewall logs"
    echo "  status          - Show container status"
    echo "  cleanup         - Stop and remove all containers"
    echo "  help            - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 build          # Build the image"
    echo "  $0 run            # Run with docker-compose (web + MAC + IP + firewall)"
    echo "  $0 run-web        # Run web app only"
    echo "  $0 run-mac        # Run MAC rotator only"
    echo "  $0 run-ip         # Run IP rotator only"
    echo "  $0 run-firewall   # Run firewall only"
    echo "  $0 logs           # View web app logs"
    echo "  $0 mac-logs       # View MAC rotator logs"
    echo "  $0 ip-logs        # View IP rotator logs"
    echo "  $0 firewall-logs  # View firewall logs"
}

# Main script logic
case "${1:-help}" in
    build)
        build
        ;;
    run)
        build
        run_compose
        ;;
    run-docker)
        build
        run_docker
        ;;
    run-web)
        build
        run_web_only
        ;;
    run-mac)
        build
        run_mac_only
        ;;
    run-ip)
        build
        run_ip_only
        ;;
    run-firewall)
        build
        run_firewall_only
        ;;
    start)
        run_compose
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        run_compose
        ;;
    logs)
        show_logs
        ;;
    mac-logs)
        show_mac_logs
        ;;
    ip-logs)
        show_ip_logs
        ;;
    firewall-logs)
        show_firewall_logs
        ;;
    status)
        status
        ;;
    cleanup)
        cleanup
        ;;
    help|*)
        show_help
        ;;
esac
