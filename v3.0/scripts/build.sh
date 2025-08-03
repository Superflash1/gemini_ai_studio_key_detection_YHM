#!/bin/bash

# Gemini Key Checker - 本地构建脚本
# 此脚本用于在本地环境构建Docker镜像

set -e  # 遇到错误时退出

# 配置变量
IMAGE_NAME="gemini-key-checker"
IMAGE_TAG="latest"
BUILD_CONTEXT="."

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

# 检查Docker是否安装
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

# 清理旧的镜像和容器
cleanup() {
    print_info "清理旧的镜像和容器..."
    
    # 停止并删除同名容器
    if docker ps -a --format 'table {{.Names}}' | grep -q "^${IMAGE_NAME}$"; then
        print_warning "停止并删除现有容器: ${IMAGE_NAME}"
        docker stop "${IMAGE_NAME}" 2>/dev/null || true
        docker rm "${IMAGE_NAME}" 2>/dev/null || true
    fi
    
    # 删除同名镜像
    if docker images --format 'table {{.Repository}}:{{.Tag}}' | grep -q "^${IMAGE_NAME}:${IMAGE_TAG}$"; then
        print_warning "删除现有镜像: ${IMAGE_NAME}:${IMAGE_TAG}"
        docker rmi "${IMAGE_NAME}:${IMAGE_TAG}" 2>/dev/null || true
    fi
    
    print_success "清理完成"
}

# 构建Docker镜像
build_image() {
    print_info "开始构建Docker镜像..."
    print_info "镜像名称: ${IMAGE_NAME}:${IMAGE_TAG}"
    print_info "构建上下文: ${BUILD_CONTEXT}"
    
    # 构建镜像
    if docker build \
        --tag "${IMAGE_NAME}:${IMAGE_TAG}" \
        --file Dockerfile \
        "${BUILD_CONTEXT}"; then
        print_success "镜像构建成功: ${IMAGE_NAME}:${IMAGE_TAG}"
    else
        print_error "镜像构建失败"
        exit 1
    fi
}

# 显示镜像信息
show_image_info() {
    print_info "镜像信息:"
    docker images "${IMAGE_NAME}:${IMAGE_TAG}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
}

# 测试镜像
test_image() {
    print_info "测试镜像..."
    
    # 检查镜像是否可以启动
    if docker run --rm --name "${IMAGE_NAME}-test" "${IMAGE_NAME}:${IMAGE_TAG}" python -c "import app; print('✅ 应用导入成功')"; then
        print_success "镜像测试通过"
    else
        print_error "镜像测试失败"
        exit 1
    fi
}

# 主函数
main() {
    print_info "=== Gemini Key Checker Docker构建脚本 ==="
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            --name)
                IMAGE_NAME="$2"
                shift 2
                ;;
            --no-cleanup)
                SKIP_CLEANUP=true
                shift
                ;;
            --no-test)
                SKIP_TEST=true
                shift
                ;;
            -h|--help)
                echo "用法: $0 [选项]"
                echo "选项:"
                echo "  --tag TAG        设置镜像标签 (默认: latest)"
                echo "  --name NAME      设置镜像名称 (默认: gemini-key-checker)"
                echo "  --no-cleanup     跳过清理步骤"
                echo "  --no-test        跳过测试步骤"
                echo "  -h, --help       显示帮助信息"
                exit 0
                ;;
            *)
                print_error "未知参数: $1"
                exit 1
                ;;
        esac
    done
    
    # 执行构建流程
    check_docker
    
    if [[ "${SKIP_CLEANUP}" != "true" ]]; then
        cleanup
    fi
    
    build_image
    show_image_info
    
    if [[ "${SKIP_TEST}" != "true" ]]; then
        test_image
    fi
    
    print_success "=== 构建完成 ==="
    print_info "运行容器: docker run -d --name ${IMAGE_NAME} -p 5000:5000 ${IMAGE_NAME}:${IMAGE_TAG}"
    print_info "查看日志: docker logs -f ${IMAGE_NAME}"
    print_info "停止容器: docker stop ${IMAGE_NAME}"
}

# 执行主函数
main "$@" 