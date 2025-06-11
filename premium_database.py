import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class PremiumDatabase:
    """Класс для управления премиум-подписками"""
    
    def __init__(self, file_path: str = "premium_users.json"):
        self.file_path = file_path
        self.users: Dict = {}
        self.load_users()
    
    def load_users(self) -> None:
        """Загружает данные пользователей из файла"""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
                    # Конвертируем ключи в строки для безопасности
                    self.users = {str(k): v for k, v in self.users.items() if k != "example_comment"}
                logger.info(f"Загружены данные о {len(self.users)} премиум-пользователях")
            else:
                self.users = {}
                logger.info("Файл премиум-пользователей не найден, создается новый")
        except Exception as e:
            logger.error(f"Ошибка загрузки файла премиум-пользователей: {e}")
            self.users = {}
    
    def save_users(self) -> None:
        """Сохраняет данные пользователей в файл"""
        try:
            # Создаем резервную копию
            if os.path.exists(self.file_path):
                backup_path = f"{self.file_path}.backup"
                # Удаляем старый бэкап, если он существует
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                os.rename(self.file_path, backup_path)
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Сохранены данные о {len(self.users)} премиум-пользователях")
        except Exception as e:
            logger.error(f"Ошибка сохранения файла премиум-пользователей: {e}")
    
    def add_premium_user(self, user_id: int, transaction_id: str = None, duration_days: int = 30) -> bool:
        """Добавляет премиум-пользователя (переводит с демо на полную версию)"""
        try:
            user_str = str(user_id)
            current_time = datetime.now()
            expire_time = current_time + timedelta(days=duration_days)
            
            # Сохраняем информацию о том, что пользователь уже использовал демо
            existing_data = self.users.get(user_str, {})
            demo_used = existing_data.get("demo_used", False)
            
            self.users[user_str] = {
                "is_premium": True,
                "is_demo": False,  # Это полная версия
                "demo_used": demo_used,  # Сохраняем историю
                "activated_at": current_time.isoformat(),
                "expires_at": expire_time.isoformat(),
                "transaction_id": transaction_id,
                "duration_days": duration_days
            }
            
            self.save_users()
            logger.info(f"Добавлен премиум-пользователь {user_id} до {expire_time.strftime('%Y-%m-%d')}")
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления премиум-пользователя {user_id}: {e}")
            return False
    
    def check_premium_status(self, user_id: int) -> Tuple[bool, str]:
        """Проверяет премиум-статус пользователя (включая демо)"""
        user_str = str(user_id)
        user_data = self.users.get(user_str, {})
        
        if not user_data.get("is_premium", False):
            return False, "free"
        
        # Проверяем срок действия
        expire_str = user_data.get("expires_at")
        if expire_str:
            try:
                expire_time = datetime.fromisoformat(expire_str)
                if datetime.now() > expire_time:
                    # Подписка истекла
                    self.users[user_str]["is_premium"] = False
                    self.save_users()
                    logger.info(f"Премиум-подписка пользователя {user_id} истекла")
                    return False, "expired"
                else:
                    # Подписка активна - проверяем тип
                    if user_data.get("is_demo", False):
                        return True, "demo"
                    else:
                        return True, "premium"
            except ValueError:
                logger.error(f"Неверный формат даты для пользователя {user_id}")
                return False, "error"
        
        return True, "premium"
    
    def activate_demo(self, user_id: int) -> Tuple[bool, str]:
        """Активирует 14-дневную демо-версию"""
        try:
            user_str = str(user_id)
            user_data = self.users.get(user_str, {})
            
            # Проверяем, не использовал ли пользователь уже демо
            if user_data.get("demo_used", False):
                return False, "❌ Вы уже использовали демо-версию ранее"
            
            # Проверяем, нет ли уже активной подписки
            is_premium, status = self.check_premium_status(user_id)
            if is_premium:
                return False, f"❌ У вас уже есть активная {'демо-' if status == 'demo' else ''}подписка"
            
            now = datetime.now()
            expires_at = now + timedelta(days=14)
            
            self.users[user_str] = {
                "is_premium": True,
                "is_demo": True,
                "demo_used": True,
                "activated_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
                "duration_days": 14,
                "transaction_id": f"demo_{int(now.timestamp())}"
            }
            
            self.save_users()
            logger.info(f"Activated 14-day demo for user {user_id} until {expires_at}")
            return True, f"🎉 Демо-режим активирован до {expires_at.strftime('%d.%m.%Y %H:%M')}"
            
        except Exception as e:
            logger.error(f"Error activating demo for user {user_id}: {e}")
            return False, "❌ Ошибка при активации демо-режима"
    
    def can_activate_demo(self, user_id: int) -> bool:
        """Проверяет, может ли пользователь активировать демо"""
        user_str = str(user_id)
        user_data = self.users.get(user_str, {})
        
        # Уже использовал демо
        if user_data.get("demo_used", False):
            return False
        
        # Уже есть активная подписка
        is_premium, _ = self.check_premium_status(user_id)
        if is_premium:
            return False
            
        return True
    
    def extend_premium(self, user_id: int, days: int) -> bool:
        """Продлевает премиум-подписку"""
        try:
            user_str = str(user_id)
            if user_str not in self.users:
                return self.add_premium_user(user_id, duration_days=days)
            
            current_expire = self.users[user_str].get("expires_at")
            if current_expire:
                expire_time = datetime.fromisoformat(current_expire)
                # Если подписка еще действует, продлеваем от текущей даты истечения
                if expire_time > datetime.now():
                    new_expire = expire_time + timedelta(days=days)
                else:
                    # Если истекла, продлеваем от текущей даты
                    new_expire = datetime.now() + timedelta(days=days)
            else:
                new_expire = datetime.now() + timedelta(days=days)
            
            self.users[user_str]["expires_at"] = new_expire.isoformat()
            self.users[user_str]["is_premium"] = True
            self.save_users()
            
            logger.info(f"Продлена премиум-подписка для {user_id} до {new_expire.strftime('%Y-%m-%d')}")
            return True
        except Exception as e:
            logger.error(f"Ошибка продления подписки для {user_id}: {e}")
            return False
    
    def get_user_info(self, user_id: int) -> Optional[Dict]:
        """Получает полную информацию о пользователе"""
        user_str = str(user_id)
        return self.users.get(user_str)
    
    def get_stats(self) -> Dict:
        """Получает статистику по премиум-пользователям и демо"""
        total_users = len(self.users)
        active_premium = 0
        active_demo = 0
        expired_premium = 0
        demo_used_count = 0
        
        current_time = datetime.now()
        
        for user_data in self.users.values():
            # Считаем использованные демо
            if user_data.get("demo_used", False):
                demo_used_count += 1
                
            if user_data.get("is_premium", False):
                expire_str = user_data.get("expires_at")
                if expire_str:
                    try:
                        expire_time = datetime.fromisoformat(expire_str)
                        if expire_time > current_time:
                            if user_data.get("is_demo", False):
                                active_demo += 1
                            else:
                                active_premium += 1
                        else:
                            expired_premium += 1
                    except ValueError:
                        expired_premium += 1
                else:
                    active_premium += 1
        
        return {
            "total_users": total_users,
            "active_premium": active_premium,
            "active_demo": active_demo,
            "expired_premium": expired_premium,
            "demo_used_total": demo_used_count,
            "free_users": total_users - active_premium - active_demo - expired_premium
        }
    
    def cleanup_expired(self) -> int:
        """Очищает истекшие подписки"""
        cleaned = 0
        current_time = datetime.now()
        
        for user_id, user_data in list(self.users.items()):
            expire_str = user_data.get("expires_at")
            if expire_str:
                try:
                    expire_time = datetime.fromisoformat(expire_str)
                    if expire_time < current_time and user_data.get("is_premium", False):
                        self.users[user_id]["is_premium"] = False
                        self.users[user_id]["is_demo"] = False  # Снимаем и демо-флаг
                        cleaned += 1
                except ValueError:
                    continue
        
        if cleaned > 0:
            self.save_users()
            logger.info(f"Очищено {cleaned} истекших подписок")
        
        return cleaned
    
    def get_expiring_soon(self, days_ahead: int = 3) -> list:
        """Получает список пользователей, у которых подписка истекает в ближайшие дни"""
        expiring_users = []
        current_time = datetime.now()
        threshold_time = current_time + timedelta(days=days_ahead)
        
        for user_id, user_data in self.users.items():
            if not user_data.get("is_premium", False):
                continue
                
            expire_str = user_data.get("expires_at")
            if expire_str:
                try:
                    expire_time = datetime.fromisoformat(expire_str)
                    if current_time < expire_time <= threshold_time:
                        expiring_users.append({
                            "user_id": int(user_id),
                            "expires_at": expire_time,
                            "is_demo": user_data.get("is_demo", False),
                            "days_left": (expire_time - current_time).days
                        })
                except ValueError:
                    continue
        
        return expiring_users

# Глобальный экземпляр для использования в боте
premium_db = PremiumDatabase() 