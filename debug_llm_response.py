#!/usr/bin/env python3
"""
Скрипт для отладки проблемы с пропаданием ответов LLM
"""

import sys
import traceback
from typing import Any, Dict, Generator

def debug_llm_wrapper(original_chat_method):
    """
    Обертка для отладки метода chat() интерпретера
    """
    def wrapper(*args, **kwargs):
        print("🔍 DEBUG: Начинаю генерацию ответа LLM...")
        print(f"🔍 DEBUG: args={args}")
        print(f"🔍 DEBUG: kwargs={kwargs}")
        
        try:
            # Вызываем оригинальный метод
            response = original_chat_method(*args, **kwargs)
            
            # Если это генератор (stream=True)
            if hasattr(response, '__iter__') and not isinstance(response, (str, bytes)):
                print("🔍 DEBUG: Получен потоковый ответ (generator)")
                
                def debug_generator():
                    chunk_count = 0
                    for chunk in response:
                        chunk_count += 1
                        print(f"🔍 DEBUG: Chunk #{chunk_count}: {chunk}")
                        yield chunk
                    print(f"🔍 DEBUG: Всего получено {chunk_count} chunks")
                
                return debug_generator()
            else:
                print(f"🔍 DEBUG: Получен обычный ответ: {response}")
                return response
                
        except Exception as e:
            print(f"❌ DEBUG: ОШИБКА при генерации ответа LLM: {e}")
            print("❌ DEBUG: Полный traceback:")
            traceback.print_exc()
            raise
    
    return wrapper

def patch_interpreter():
    """
    Патчит Open Interpreter для отладки
    """
    try:
        import interpreter
        
        # Патчим метод chat
        if hasattr(interpreter, 'chat'):
            print("🔧 Патчу interpreter.chat()...")
            interpreter.chat = debug_llm_wrapper(interpreter.chat)
        
        # Патчим метод respond, если есть
        if hasattr(interpreter, 'respond'):
            print("🔧 Патчу interpreter.respond()...")
            interpreter.respond = debug_llm_wrapper(interpreter.respond)
            
        # Патчим core.respond, если есть
        if hasattr(interpreter, 'core') and hasattr(interpreter.core, 'respond'):
            print("🔧 Патчу interpreter.core.respond()...")
            interpreter.core.respond = debug_llm_wrapper(interpreter.core.respond)
            
        print("✅ Патчинг завершен!")
        return interpreter
        
    except ImportError as e:
        print(f"❌ Не удалось импортировать interpreter: {e}")
        return None

def monitor_terminal_interface():
    """
    Мониторинг терминального интерфейса
    """
    try:
        from interpreter.terminal_interface.terminal_interface import terminal_interface
        
        def debug_terminal_interface(*args, **kwargs):
            print("🖥️  DEBUG: Вызван terminal_interface")
            print(f"🖥️  DEBUG: args={args}")
            print(f"🖥️  DEBUG: kwargs={kwargs}")
            
            try:
                result = terminal_interface(*args, **kwargs)
                print("🖥️  DEBUG: terminal_interface завершен успешно")
                return result
            except Exception as e:
                print(f"❌ DEBUG: Ошибка в terminal_interface: {e}")
                traceback.print_exc()
                raise
        
        # Заменяем оригинальную функцию
        import interpreter.terminal_interface.terminal_interface
        interpreter.terminal_interface.terminal_interface.terminal_interface = debug_terminal_interface
        
        print("🖥️  Патчинг terminal_interface завершен!")
        
    except ImportError as e:
        print(f"❌ Не удалось импортировать terminal_interface: {e}")

if __name__ == "__main__":
    print("🚀 Запуск отладочного скрипта...")
    
    # Патчим интерпретер
    interpreter = patch_interpreter()
    
    # Патчим терминальный интерфейс
    monitor_terminal_interface()
    
    if interpreter:
        print("✅ Отладка активирована! Теперь запустите вашу программу.")
        print("📝 Все вызовы LLM будут логироваться с префиксом '🔍 DEBUG:'")
    else:
        print("❌ Не удалось активировать отладку")
        sys.exit(1)