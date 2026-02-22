# TempCleaner (Windows) — MVP
Простая утилита для очистки временных файлов на Windows 10/11.

## Возможности
- Очистка **пользовательского TEMP** (`%TEMP%`)
- (опционально) очистка **системного TEMP** (`C:\Windows\Temp`) — если есть доступ
- (опционально) очистка **Prefetch** (`C:\Windows\Prefetch`) — обычно нужен админ
- Режим **dry-run** (показывает что будет удалено)
- Фильтр по возрасту файлов: удалить только старше N дней (0 = всё)
- Отчёт: сколько удалено и сколько места освобождено

> Безопасность: по умолчанию включён dry-run и удаление только старше 1 дня.

## 📦 Download

➡ **[Download TempCleaner for Windows](https://github.com/<kirillsql1kaa11>/temp-cleaner/releases/latest)**

Просто распакуй и запусти `TempCleaner.exe`.

## Запуск (GUI)
```powershell
python -m temp_cleaner.gui
```

## Запуск (CLI)
```powershell
python -m temp_cleaner.cli targets
python -m temp_cleaner.cli clean --target user --older-days 1 --dry-run
python -m temp_cleaner.cli clean --target user --older-days 1 --no-dry-run
```

