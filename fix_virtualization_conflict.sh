#!/bin/bash

# Скрипт для исправления конфликта VirtualBox и Android Emulator
# Автор: AI Assistant

echo "=== Исправление конфликта VirtualBox и Android Emulator ==="

# Проверяем, запущен ли VirtualBox
echo "Проверяем запущенные VMs..."
VBoxManage list runningvms

echo ""
echo "Выберите вариант исправления:"
echo "1) Отключить эксклюзивную виртуализацию VirtualBox (рекомендуется)"
echo "2) Остановить VMs и выгрузить модули VirtualBox"
echo "3) Показать информацию для ручного исправления"
echo ""

read -p "Введите номер варианта (1-3): " choice

case $choice in
    1)
        echo "Отключаем эксклюзивную виртуализацию..."
        
        # Сохраняем состояние запущенных VMs
        VBoxManage list runningvms | while IFS= read -r line; do
            if [[ $line =~ \"(.*)\"[[:space:]]+\{(.*)\} ]]; then
                vm_name="${BASH_REMATCH[1]}"
                echo "Сохраняем состояние VM: $vm_name"
                VBoxManage controlvm "$vm_name" savestate
            fi
        done
        
        # Отключаем эксклюзивную виртуализацию
        VBoxManage setextradata global "VBoxInternal/Config/ExclusiveHWVirt" "false"
        
        echo "Готово! Теперь можно запускать Android Emulator одновременно с VirtualBox."
        echo "Для запуска VM обратно используйте: VBoxManage startvm \"Имя VM\""
        ;;
        
    2)
        echo "Останавливаем VMs и выгружаем модули..."
        
        # Останавливаем все запущенные VMs
        VBoxManage list runningvms | while IFS= read -r line; do
            if [[ $line =~ \"(.*)\"[[:space:]]+\{(.*)\} ]]; then
                vm_name="${BASH_REMATCH[1]}"
                echo "Останавливаем VM: $vm_name"
                VBoxManage controlvm "$vm_name" savestate
            fi
        done
        
        # Выгружаем модули VirtualBox
        echo "Выгружаем модули VirtualBox..."
        sudo modprobe -r vboxnetflt vboxnetadp vboxdrv 2>/dev/null || true
        
        echo "Готово! Теперь можно запускать Android Emulator."
        echo "Для возврата VirtualBox выполните:"
        echo "sudo modprobe vboxdrv vboxnetadp vboxnetflt"
        ;;
        
    3)
        echo ""
        echo "=== Информация для ручного исправления ==="
        echo ""
        echo "Проблема: VirtualBox и Android Emulator конфликтуют за доступ к аппаратной виртуализации"
        echo ""
        echo "Текущая конфигурация VirtualBox:"
        echo "- exclusiveHwVirt=true (блокирует другие гипервизоры)"
        echo "- Загружены модули: vboxdrv, kvm_amd, kvm"
        echo ""
        echo "Решения:"
        echo "1. Отключить эксклюзивность: VBoxManage setextradata global \"VBoxInternal/Config/ExclusiveHWVirt\" \"false\""
        echo "2. Использовать программную эмуляцию: emulator -avd имя_avd -accel off"
        echo "3. Последовательное использование (не одновременно)"
        echo ""
        echo "Для проверки AVD: emulator -list-avds"
        echo "Для проверки эмулятора: emulator -accel-check"
        ;;
        
    *)
        echo "Неверный выбор. Выход."
        exit 1
        ;;
esac

echo ""
echo "Скрипт завершен."