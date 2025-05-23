from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class ChatMessage:
    sender_id: str
    sender_name: str
    content: str
    timestamp: datetime
    message_type: str  # 'chat', 'system', 'notification'
    target: Optional[str] = None  # Pour les messages privés

class ChatSystem:
    def __init__(self, max_history_size: int = 100):
        self.max_history_size = max_history_size
        self.messages: List[ChatMessage] = []
        self.private_messages: Dict[str, List[ChatMessage]] = {}
        
    def add_message(self, message: ChatMessage) -> None:
        """Ajoute un message à l'historique"""
        if message.message_type == 'chat':
            self.messages.append(message)
            if len(self.messages) > self.max_history_size:
                self.messages.pop(0)
        elif message.message_type == 'private' and message.target:
            if message.target not in self.private_messages:
                self.private_messages[message.target] = []
            self.private_messages[message.target].append(message)
            if len(self.private_messages[message.target]) > self.max_history_size:
                self.private_messages[message.target].pop(0)
    
    def get_messages(self, count: int = 50) -> List[ChatMessage]:
        """Récupère les derniers messages"""
        return self.messages[-count:]
    
    def get_private_messages(self, user_id: str, count: int = 50) -> List[ChatMessage]:
        """Récupère les derniers messages privés d'un utilisateur"""
        if user_id not in self.private_messages:
            return []
        return self.private_messages[user_id][-count:]
    
    def clear_history(self) -> None:
        """Efface l'historique des messages"""
        self.messages.clear()
        self.private_messages.clear()

class NotificationSystem:
    def __init__(self):
        self.notifications: List[ChatMessage] = []
        
    def add_notification(self, content: str, target: Optional[str] = None) -> None:
        """Ajoute une notification"""
        notification = ChatMessage(
            sender_id="system",
            sender_name="Système",
            content=content,
            timestamp=datetime.now(),
            message_type="notification",
            target=target
        )
        self.notifications.append(notification)
        
    def get_notifications(self, user_id: Optional[str] = None, count: int = 10) -> List[ChatMessage]:
        """Récupère les dernières notifications"""
        if user_id:
            return [
                n for n in self.notifications 
                if n.target is None or n.target == user_id
            ][-count:]
        return self.notifications[-count:]
    
    def clear_notifications(self) -> None:
        """Efface les notifications"""
        self.notifications.clear()

class ChatManager:
    def __init__(self, max_history_size: int = 100):
        self.chat = ChatSystem(max_history_size)
        self.notifications = NotificationSystem()
        
    def send_message(self, sender_id: str, sender_name: str, content: str, 
                    message_type: str = 'chat', target: Optional[str] = None) -> ChatMessage:
        """Envoie un message"""
        message = ChatMessage(
            sender_id=sender_id,
            sender_name=sender_name,
            content=content,
            timestamp=datetime.now(),
            message_type=message_type,
            target=target
        )
        self.chat.add_message(message)
        return message
    
    def send_notification(self, content: str, target: Optional[str] = None) -> None:
        """Envoie une notification"""
        self.notifications.add_notification(content, target)
    
    def get_messages(self, count: int = 50) -> List[ChatMessage]:
        """Récupère les derniers messages"""
        return self.chat.get_messages(count)
    
    def get_private_messages(self, user_id: str, count: int = 50) -> List[ChatMessage]:
        """Récupère les derniers messages privés"""
        return self.chat.get_private_messages(user_id, count)
    
    def get_notifications(self, user_id: Optional[str] = None, count: int = 10) -> List[ChatMessage]:
        """Récupère les dernières notifications"""
        return self.notifications.get_notifications(user_id, count)
    
    def clear_all(self) -> None:
        """Efface tous les messages et notifications"""
        self.chat.clear_history()
        self.notifications.clear_notifications()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'état du chat en dictionnaire"""
        return {
            'messages': [
                {
                    'sender_id': msg.sender_id,
                    'sender_name': msg.sender_name,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'message_type': msg.message_type,
                    'target': msg.target
                }
                for msg in self.chat.messages
            ],
            'private_messages': {
                user_id: [
                    {
                        'sender_id': msg.sender_id,
                        'sender_name': msg.sender_name,
                        'content': msg.content,
                        'timestamp': msg.timestamp.isoformat(),
                        'message_type': msg.message_type,
                        'target': msg.target
                    }
                    for msg in messages
                ]
                for user_id, messages in self.chat.private_messages.items()
            },
            'notifications': [
                {
                    'sender_id': notif.sender_id,
                    'sender_name': notif.sender_name,
                    'content': notif.content,
                    'timestamp': notif.timestamp.isoformat(),
                    'message_type': notif.message_type,
                    'target': notif.target
                }
                for notif in self.notifications.notifications
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatManager':
        """Crée un ChatManager à partir d'un dictionnaire"""
        manager = cls()
        
        # Restaure les messages
        for msg_data in data.get('messages', []):
            message = ChatMessage(
                sender_id=msg_data['sender_id'],
                sender_name=msg_data['sender_name'],
                content=msg_data['content'],
                timestamp=datetime.fromisoformat(msg_data['timestamp']),
                message_type=msg_data['message_type'],
                target=msg_data.get('target')
            )
            manager.chat.messages.append(message)
        
        # Restaure les messages privés
        for user_id, messages_data in data.get('private_messages', {}).items():
            manager.chat.private_messages[user_id] = [
                ChatMessage(
                    sender_id=msg_data['sender_id'],
                    sender_name=msg_data['sender_name'],
                    content=msg_data['content'],
                    timestamp=datetime.fromisoformat(msg_data['timestamp']),
                    message_type=msg_data['message_type'],
                    target=msg_data.get('target')
                )
                for msg_data in messages_data
            ]
        
        # Restaure les notifications
        for notif_data in data.get('notifications', []):
            notification = ChatMessage(
                sender_id=notif_data['sender_id'],
                sender_name=notif_data['sender_name'],
                content=notif_data['content'],
                timestamp=datetime.fromisoformat(notif_data['timestamp']),
                message_type=notif_data['message_type'],
                target=notif_data.get('target')
            )
            manager.notifications.notifications.append(notification)
        
        return manager 