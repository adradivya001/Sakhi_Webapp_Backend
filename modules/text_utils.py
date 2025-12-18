# modules/text_utils.py
"""
Utility functions for text processing.
"""

MAX_RESPONSE_LENGTH = 2000


def truncate_response(text: str, max_length: int = MAX_RESPONSE_LENGTH) -> str:
    """
    Truncate text to a maximum character length.
    
    For responses containing "Follow ups :", only the main reply (before the follow-ups)
    is counted towards the character limit. The follow-ups section is preserved as-is.
    
    Args:
        text: The text to truncate
        max_length: Maximum allowed length for the main reply (default: 1024)
    
    Returns:
        Truncated text with main reply within max_length, follow-ups preserved
    """
    if not text:
        return text
    
    # Check if response contains follow-up questions
    follow_ups_marker = " Follow ups : "
    
    if follow_ups_marker in text:
        # Split into main reply and follow-ups
        parts = text.split(follow_ups_marker, 1)
        main_reply = parts[0]
        follow_ups = follow_ups_marker + parts[1] if len(parts) > 1 else ""
        
        # Only truncate the main reply if it exceeds max_length
        if len(main_reply) > max_length:
            main_reply = _truncate_text(main_reply, max_length)
        
        # Recombine main reply with follow-ups
        return main_reply + follow_ups
    else:
        # No follow-ups, truncate normally if needed
        if len(text) <= max_length:
            return text
        return _truncate_text(text, max_length)


def _truncate_text(text: str, max_length: int) -> str:
    """
    Internal helper to truncate text at a sentence boundary.
    
    Args:
        text: The text to truncate
        max_length: Maximum allowed length
    
    Returns:
        Truncated text
    """
    # Truncate to max_length - 3 to add ellipsis
    truncated = text[:max_length - 3].rstrip()
    
    # Try to truncate at a sentence boundary for better readability
    # Look for the last sentence ending punctuation
    last_period = truncated.rfind('.')
    last_exclamation = truncated.rfind('!')
    last_question = truncated.rfind('?')
    last_newline = truncated.rfind('\n')
    
    # Find the latest sentence boundary
    sentence_end = max(last_period, last_exclamation, last_question, last_newline)
    
    # If we found a sentence boundary within reasonable distance (not too far back)
    # use it, otherwise just use the hard truncation
    if sentence_end > max_length * 0.7:  # Within last 30% of text
        truncated = truncated[:sentence_end + 1]
    else:
        # Add ellipsis to indicate truncation
        truncated += "..."
    
    return truncated
