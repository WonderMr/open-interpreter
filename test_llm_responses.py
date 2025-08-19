#!/usr/bin/env python3
"""
Воспроизводимый тест для проверки работы LLM ответов
Тестирует:
1. Запрос имени операционной системы  
2. Запрос открытых TCP-портов 3 способами
"""

import sys
import os

# Добавляем путь к интерпретеру
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import interpreter
except ImportError:
    print("❌ Не удалось импортировать interpreter")
    print("Убедитесь, что вы находитесь в директории open-interpreter")
    sys.exit(1)

def test_llm_responses():
    """
    Тест для проверки корректной работы LLM ответов
    """
    print("🚀 Запуск теста LLM ответов...")
    
    # Настройка интерпретера
    interpreter.verbose = True  # Включаем подробный вывод для отладки
    interpreter.auto_run = True  # Автоматически выполняем код
    interpreter.offline = False  # Используем онлайн модель
    
    # Тестовые запросы
    test_queries = [
        {
            "name": "Тест 1: Запрос операционной системы",
            "query": "Привет, какая у меня ос?",
            "expected_commands": ["uname", "cat /etc/os-release"]
        },
        {
            "name": "Тест 2: TCP-порты тремя способами", 
            "query": "Привет, выполни три разных скрипта для получения информации об открытых TCP-портах",
            "expected_commands": ["ss", "lsof", "netstat"]
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"🧪 {test['name']}")
        print(f"{'='*60}")
        
        print(f"📝 Запрос: {test['query']}")
        print(f"⏳ Ожидаем выполнения...")
        
        try:
            # Сброс сообщений для чистого теста
            interpreter.messages = []
            
            # Счетчики для анализа
            chunks_received = 0
            message_chunks = 0
            code_chunks = 0
            console_chunks = 0
            has_llm_response = False
            
            print(f"\n🔄 Отправляем запрос LLM...")
            
            # Выполняем запрос
            for chunk in interpreter.chat(test['query'], stream=True):
                chunks_received += 1
                
                if chunk.get('type') == 'message':
                    message_chunks += 1
                    has_llm_response = True
                    print(f"💬 LLM ответ (chunk {message_chunks}): {chunk.get('content', '')[:100]}...")
                    
                elif chunk.get('type') == 'code':
                    code_chunks += 1
                    print(f"💻 Код (chunk {code_chunks}): {chunk.get('format', 'unknown')} - {chunk.get('content', '')[:50]}...")
                    
                elif chunk.get('type') == 'console':
                    console_chunks += 1
                    if chunk.get('format') == 'output':
                        print(f"📟 Вывод (chunk {console_chunks}): {chunk.get('content', '')[:100]}...")
            
            # Анализ результатов
            test_result = {
                "name": test['name'],
                "success": has_llm_response,
                "chunks_total": chunks_received,
                "message_chunks": message_chunks,
                "code_chunks": code_chunks, 
                "console_chunks": console_chunks,
                "error": None
            }
            
            if has_llm_response:
                print(f"✅ Тест {i} ПРОЙДЕН - получены ответы LLM")
            else:
                print(f"❌ Тест {i} ПРОВАЛЕН - ответы LLM не получены!")
                
            results.append(test_result)
            
        except Exception as e:
            print(f"❌ Тест {i} ПРОВАЛЕН с ошибкой: {e}")
            import traceback
            traceback.print_exc()
            
            results.append({
                "name": test['name'],
                "success": False,
                "chunks_total": 0,
                "message_chunks": 0,
                "code_chunks": 0,
                "console_chunks": 0,
                "error": str(e)
            })
    
    # Итоговый отчет
    print(f"\n{'='*60}")
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print(f"{'='*60}")
    
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"Пройдено тестов: {passed}/{total}")
    
    for result in results:
        status = "✅ ПРОЙДЕН" if result['success'] else "❌ ПРОВАЛЕН"
        print(f"\n{status} - {result['name']}")
        print(f"  Всего chunks: {result['chunks_total']}")
        print(f"  Message chunks: {result['message_chunks']}")
        print(f"  Code chunks: {result['code_chunks']}")
        print(f"  Console chunks: {result['console_chunks']}")
        if result['error']:
            print(f"  Ошибка: {result['error']}")
    
    if passed == total:
        print(f"\n🎉 Все тесты пройдены! LLM ответы работают корректно.")
        return True
    else:
        print(f"\n⚠️  {total - passed} тестов провалено. Проблема с LLM ответами!")
        return False

def quick_test():
    """
    Быстрый тест одного запроса
    """
    print("🚀 Быстрый тест...")
    
    interpreter.verbose = True
    interpreter.auto_run = True
    
    print("📝 Тестовый запрос: 'Привет, какая у меня ос?'")
    
    chunks = list(interpreter.chat("Привет, какая у меня ос?", stream=True))
    
    message_chunks = [c for c in chunks if c.get('type') == 'message']
    
    if message_chunks:
        print("✅ LLM ответы работают!")
        print(f"Получено {len(message_chunks)} message chunks")
    else:
        print("❌ LLM ответы НЕ работают!")
        print(f"Всего chunks: {len(chunks)}")
        print("Типы chunks:", [c.get('type') for c in chunks])

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_test()
    else:
        test_llm_responses()