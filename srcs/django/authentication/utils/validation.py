def validate_printable_chars(text):
    """Valida que el texto solo contenga caracteres imprimibles y no espacios"""
    if not text:
        return False
    # Comprobar espacios y tabulaciones
    if any(char.isspace() for char in text):
        return False
    # Validar que todos los caracteres sean imprimibles
    return all(char.isprintable() and not char.isspace() for char in text)