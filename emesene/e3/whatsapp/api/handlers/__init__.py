__all__ = [
    'sasl', # Logging in
    'ping', # Keeping connection alive
    'last_seen', # Response to last seen requests
    'message_text', # Text message received
    'message_ack_request', # Send received acks
    'message_received_server', # Our message was received by the server
    'message_received_client', # Our message was received by destination client
    'message_chatstate', # XMPP chatstates (other user is typing, ...)
    'group_info', # Info about a groupchat (owner, creation date, ...)
    'group_participants', # Members of a groupchat
    'group_presences', # Leaving and joining of users
    'group_subject', # Subject of group chats
]
