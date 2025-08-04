#!/bin/bash

# Gemini Key Checker - 部署脚本
# 此脚本用于快速部署应用

set -e  # 遇到错误时退出

# 配置变量
CONTAINER_NAME="gemini-key-checker"
IMAGE_NAME="gemini-key-checker"
IMAGE_TAG="latest"
PORT="5000"
VOLUME_NAME="gemini_data"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${2}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

print_info() {
    print_message "$1" "$BLUE"
}

print_success() {
    print_message "$1" "$GREEN"
}

print_warning() {
    print_message "$1" "$YELLOW"
}

print_error() {
    print_message "$1" "$RED"
}

# 检查Docker环境
check_docker() {
    print_info "检查Docker环境..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker未运行，请启动Docker服务"
        exit 1
    fi
    
    print_success "Docker环境检查通过"
}

# 检查镜像是否存在
check_image() {
    print_info "检查镜像: ${IMAGE_NAME}:${IMAGE_TAG}"
    if ! docker images --format 'table {{.Repository}}:{{.Tag}}' | grep -q "^${IMAGE_NAME}:${IMAGE_TAG}$"; then
        print_warning "镜像不存在，正在构建..."
        if [[ -f "scripts/build.sh" ]]; then
            bash scripts/build.sh --tag "${IMAGE_TAG}" --name "${IMAGE_NAME}"
        else
            print_error "镜像不存在且构建脚本未找到，请先构建镜像"
            exit 1
        fi
    else
        print_success "镜像已存在: ${IMAGE_NAME}:${IMAGE_TAG}"
    fi
}

# 停止现有容器
stop_existing() {
    print_info "检查现有容器..."
    if docker ps -a --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_warning "停止现有容器: ${CONTAINER_NAME}"
        docker stop "${CONTAINER_NAME}" 2>/dev/null || true
        docker rm "${CONTAINER_NAME}" 2>/dev/null || true
        print_success "现有容器已停止并删除"
    else
        print_info "没有找到现有容器"
    fi
}

# 创建数据卷
create_volume() {
    print_info "检查数据卷: ${VOLUME_NAME}"
    if ! docker volume ls --format 'table {{.Name}}' | grep -q "^${VOLUME_NAME}$"; then
        print_info "创建数据卷: ${VOLUME_NAME}"
        docker volume create "${VOLUME_NAME}"
        print_success "数据卷创建成功"
    else
        print_info "数据卷已存在"
    fi
}

# 启动容器
start_container() {
    print_info "启动容器: ${CONTAINER_NAME}"
    
    docker run -d \
        --name "${CONTAINER_NAME}" \
        --restart unless-stopped \
        -p "${PORT}:5000" \
        -v "${VOLUME_NAME}:/app/instance" \
        "${IMAGE_NAME}:${IMAGE_TAG}"
    
    print_success "容器启动成功"
}

# 等待服务就绪
wait_for_service() {
    print_info "等待服务启动..."
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s "http://localhost:${PORT}/api/stats" &> /dev/null; then
            print_success "服务已就绪"
            return 0
        fi
        
        print_info "等待服务启动... (${attempt}/${max_attempts})"
        sleep 2
        ((attempt++))
    done
    
    print_error "服务启动超时"
    return 1
}

# 显示部署信息
show_deployment_info() {
    print_success "=== 部署完成 ==="
    echo ""
    print_info "🌐 访问地址:"
    echo "   本地访问: http://localhost:${PORT}"
    echo "   局域网访问: http://$(hostname -I | awk '{print $1}'):${PORT}"
    echo ""
    print_info "📊 管理命令:"
    echo "   查看容器状态: docker ps | grep ${CONTAINER_NAME}"
    echo "   查看实时日志: docker logs -f ${CONTAINER_NAME}"
    echo "   停止服务: docker stop ${CONTAINER_NAME}"
    echo "   重启服务: docker restart ${CONTAINER_NAME}"
    echo ""
    print_info "💾 数据管理:"
    echo "   数据卷名称: ${VOLUME_NAME}"
    echo "   备份数据: docker run --rm -v ${VOLUME_NAME}:/data -v \$(pwd):/backup alpine tar czf /backup/backup-\$(date +%Y%m%d_%H%M%S).tar.gz -C /data ."
    echo ""
}

# 显示容器日志
show_logs() {
    print_info "显示容器日志 (按 Ctrl+C 退出):"
    docker logs -f "${CONTAINER_NAME}"
}

# 主函数
main() {
    print_info "=== Gemini Key Checker 部署脚本 ==="
    
    # 解析命令行参数
    local show_logs_flag=false
    local force_rebuild=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --port)
                PORT="$2"
                shift 2
                ;;
            --tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            --name)
                CONTAINER_NAME="$2"
                shift 2
                ;;
            --volume)
                VOLUME_NAME="$2"
                shift 2
                ;;
            --logs)
                show_logs_flag=true
                shift
                ;;
            --rebuild)
                force_rebuild=true
                shift
                ;;
            -h|--help)
                echo "用法: $0 [选项]"
                echo "选项:"
                echo "  --port PORT      设置端口映射 (默认: 5000)"
                echo "  --tag TAG        设置镜像标签 (默认: latest)"
                echo "  --name NAME      设置容器名称 (默认: gemini-key-checker)"
                echo "  --volume VOL     设置数据卷名称 (默认: gemini_data)"
                echo "  --logs           部署后显示日志"
                echo "  --rebuild        强制重新构建镜像"
                echo "  -h, --help       显示帮助信息"
                exit 0
                ;;
            *)
                print_error "未知参数: $1"
                exit 1
                ;;
        esac
    done
    
    # 执行部署流程
    check_docker
    
    if [[ "${force_rebuild}" == "true" ]]; then
        print_info "强制重新构建镜像..."
        if [[ -f "scripts/build.sh" ]]; then
            bash scripts/build.sh --tag "${IMAGE_TAG}" --name "${IMAGE_NAME}"
        else
            print_error "构建脚本未找到"
            exit 1
        fi
    else
        check_image
    fi
    
    stop_existing
    create_volume
    start_container
    
    if wait_for_service; then
        show_deployment_info
        
        if [[ "${show_logs_flag}" == "true" ]]; then
            show_logs
        fi
    else
        print_error "部署失败，请检查容器日志"
        docker logs "${CONTAINER_NAME}"
        exit 1
    fi
}

# 执行主函数
main "$@" 