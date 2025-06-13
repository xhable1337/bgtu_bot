#!/bin/bash

# Скрипт для установки и управления systemd сервисом BGTU Telegram Bot

SERVICE_NAME="bgtu-bot"
SERVICE_TEMPLATE="systemd/bgtu-bot.service.template"
SERVICE_FILE="systemd/bgtu-bot.service"
SYSTEM_SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}.service"

# Автоматическое определение переменных окружения
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_USER="$(whoami)"
CURRENT_GROUP="$(id -gn)"

# Определение пути к Python с приоритетом виртуальной среды
PYTHON_PATH=""
VENV_DIRS=(".venv" "venv" ".env" "env")

# Проверяем наличие виртуальной среды в корне проекта
for venv_dir in "${VENV_DIRS[@]}"; do
    if [ -d "$PROJECT_DIR/$venv_dir" ]; then
        VENV_PYTHON="$PROJECT_DIR/$venv_dir/bin/python"
        if [ -x "$VENV_PYTHON" ]; then
            PYTHON_PATH="$VENV_PYTHON"
            break
        fi
    fi
done

# Если виртуальная среда не найдена, используем глобальный Python
if [ -z "$PYTHON_PATH" ]; then
    PYTHON_PATH="$(which python3)"
    echo "Используется глобальный Python"
fi

# Проверяем наличие Python
if [ -z "$PYTHON_PATH" ]; then
    echo "Ошибка: Python3 не найден в системе!"
    exit 1
fi

# Функция для проверки прав sudo
check_sudo() {
    if [ "$EUID" -ne 0 ]; then
        echo "Этот скрипт требует права администратора (sudo)"
        echo "Запустите: sudo $0 $*"
        exit 1
    fi
}

# Функция генерации файла сервиса из шаблона
generate_service_file() {
    echo "Генерация файла сервиса из шаблона..."
    echo "Проект: $PROJECT_DIR"
    echo "Пользователь: $CURRENT_USER"
    echo "Группа: $CURRENT_GROUP"
    echo "Python: $PYTHON_PATH"
    
    # Проверяем наличие шаблона
    if [ ! -f "$SERVICE_TEMPLATE" ]; then
        echo "Ошибка: Файл шаблона $SERVICE_TEMPLATE не найден!"
        exit 1
    fi
    
    # Создаем файл сервиса из шаблона с заменой переменных
    sed -e "s|{{PROJECT_DIR}}|$PROJECT_DIR|g" \
        -e "s|{{USER}}|$CURRENT_USER|g" \
        -e "s|{{GROUP}}|$CURRENT_GROUP|g" \
        -e "s|{{PYTHON_PATH}}|$PYTHON_PATH|g" \
        "$SERVICE_TEMPLATE" > "$SERVICE_FILE"
    
    if [ $? -eq 0 ]; then
        echo "Файл сервиса успешно сгенерирован: $SERVICE_FILE"
    else
        echo "Ошибка при генерации файла сервиса!"
        exit 1
    fi
}

# Функция установки сервиса
install_service() {
    echo "Установка systemd сервиса для BGTU Bot..."
    
    # Генерируем файл сервиса из шаблона
    generate_service_file
    
    # Копируем файл сервиса
    cp "$SERVICE_FILE" "$SYSTEM_SERVICE_PATH"
    
    # Устанавливаем правильные права доступа
    chmod 644 "$SYSTEM_SERVICE_PATH"
    
    # Перезагружаем systemd
    systemctl daemon-reload
    
    # Включаем автозапуск
    systemctl enable "$SERVICE_NAME"
    
    echo "Сервис успешно установлен!"
    echo "Для запуска используйте: "
    echo "  · $0 start"
    echo "  · sudo systemctl start $SERVICE_NAME"

}

# Функция удаления сервиса
uninstall_service() {
    echo "Удаление systemd сервиса BGTU Bot..."
    
    # Останавливаем сервис
    systemctl stop "$SERVICE_NAME" 2>/dev/null
    
    # Отключаем автозапуск
    systemctl disable "$SERVICE_NAME" 2>/dev/null
    
    # Удаляем файл сервиса
    rm -f "$SYSTEM_SERVICE_PATH"
    
    # Перезагружаем systemd
    systemctl daemon-reload
    
    echo "Сервис успешно удален!"
}

# Функция запуска сервиса
start_service() {
    echo "Запуск BGTU Bot сервиса..."
    systemctl start "$SERVICE_NAME"
    systemctl status "$SERVICE_NAME" --no-pager
}

# Функция остановки сервиса
stop_service() {
    echo "Остановка BGTU Bot сервиса..."
    systemctl stop "$SERVICE_NAME"
}

# Функция перезапуска сервиса
restart_service() {
    echo "Перезапуск BGTU Bot сервиса..."
    systemctl restart "$SERVICE_NAME"
    systemctl status "$SERVICE_NAME" --no-pager
}

# Функция проверки статуса сервиса
status_service() {
    systemctl status "$SERVICE_NAME" --no-pager
}

# Функция просмотра логов
logs_service() {
    journalctl -u "$SERVICE_NAME" -f
}

# Основная логика
case "$1" in
    generate)
        generate_service_file
        ;;
    install)
        check_sudo
        install_service
        ;;
    uninstall)
        check_sudo
        uninstall_service
        ;;
    start)
        check_sudo
        start_service
        ;;
    stop)
        check_sudo
        stop_service
        ;;
    restart)
        check_sudo
        restart_service
        ;;
    status)
        status_service
        ;;
    logs)
        logs_service
        ;;
    *)
        echo "Использование: $0 {generate|install|uninstall|start|stop|restart|status|logs}"
        echo ""
        echo "Команды:"
        echo "  generate  - Сгенерировать файл сервиса из шаблона"
        echo "  install   - Установить systemd сервис"
        echo "  uninstall - Удалить systemd сервис"
        echo "  start     - Запустить сервис"
        echo "  stop      - Остановить сервис"
        echo "  restart   - Перезапустить сервис"
        echo "  status    - Показать статус сервиса"
        echo "  logs      - Показать логи сервиса в реальном времени"
        echo ""
        echo "Автоматически определенные параметры:"
        echo "  Проект: $PROJECT_DIR"
        echo "  Пользователь: $CURRENT_USER"
        echo "  Группа: $CURRENT_GROUP"
        echo "  Python: $PYTHON_PATH"
        exit 1
        ;;
esac
