"""
JWT wrapper to handle different JWT implementations
"""
try:
    import PyJWT as jwt
    print("Using PyJWT as jwt")
except ImportError:
    try:
        import python_jwt as jwt
        print("Using python_jwt as jwt")
    except ImportError:
        try:
            import jwt
            print("Using jwt package directly")
        except ImportError:
            print("ERROR: No JWT implementation found!")
            raise ImportError("No JWT implementation found. Please install PyJWT, python-jwt, or jwt.")

# Export the jwt module
__all__ = ['jwt']