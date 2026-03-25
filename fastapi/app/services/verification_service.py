"""Email verification code service using Redis"""
import random
import string
from app.core.cache import cache


class VerificationService:
    """Handle email verification codes with Redis"""

    # Redis key prefixes
    KEY_CODE = "email:verify:code:{email}"
    KEY_SENT = "email:verify:sent:{email}"
    KEY_ATTEMPTS = "email:verify:attempts:{email}"

    # TTL settings (seconds)
    CODE_TTL = 600  # 10 minutes for code validity
    SENT_TTL = 60   # 60 seconds between sends
    ATTEMPTS_TTL = 600  # 10 minutes for attempt tracking
    MAX_ATTEMPTS = 3  # Max failed verification attempts

    @classmethod
    def _get_key(cls, template: str, email: str) -> str:
        """Generate Redis key for given email"""
        return template.format(email=email.lower().strip())

    @classmethod
    def generate_code(cls, length: int = 6) -> str:
        """Generate a numeric verification code"""
        return ''.join(random.choices(string.digits, k=length))

    @classmethod
    async def can_send(cls, email: str) -> tuple[bool, int]:
        """Check if verification code can be sent to email

        Returns:
            tuple: (can_send, remaining_seconds)
            - can_send: True if can send, False otherwise
            - remaining_seconds: seconds to wait if cannot send, 0 if can send
        """
        key = cls._get_key(cls.KEY_SENT, email)
        ttl = await cache.ttl(key)

        # ttl > 0 means key exists and has expiration
        if ttl > 0:
            return False, ttl

        return True, 0

    @classmethod
    async def create_code(cls, email: str) -> str:
        """Create and store verification code

        Args:
            email: Email address

        Returns:
            Generated verification code

        Raises:
            ValueError: If sending too frequently
        """
        email = email.lower().strip()

        # Check frequency limit
        can_send, remaining = await cls.can_send(email)
        if not can_send:
            raise ValueError(f"Please wait {remaining} seconds before requesting a new code")

        # Generate code
        code = cls.generate_code(6)

        # Store code with TTL
        code_key = cls._get_key(cls.KEY_CODE, email)
        await cache.set(code_key, code, ex=cls.CODE_TTL)

        # Set sent flag with TTL (frequency limit)
        sent_key = cls._get_key(cls.KEY_SENT, email)
        await cache.set(sent_key, "1", ex=cls.SENT_TTL)

        # Clear previous attempts if any
        attempts_key = cls._get_key(cls.KEY_ATTEMPTS, email)
        await cache.delete(attempts_key)

        return code

    @classmethod
    async def verify_code(cls, email: str, code: str) -> tuple[bool, str]:
        """Verify email verification code

        Args:
            email: Email address
            code: Verification code to verify

        Returns:
            tuple: (success, message)
            - success: True if verified, False otherwise
            - message: Status message
        """
        email = email.lower().strip()
        code_key = cls._get_key(cls.KEY_CODE, email)
        attempts_key = cls._get_key(cls.KEY_ATTEMPTS, email)

        # Check if code exists
        stored_code = await cache.get(code_key)
        if stored_code is None:
            return False, "Verification code expired or does not exist"

        # Check failed attempts
        attempts_str = await cache.get(attempts_key)
        attempts = int(attempts_str) if attempts_str else 0

        if attempts >= cls.MAX_ATTEMPTS:
            # Clear the code to force resend
            await cache.delete(code_key)
            await cache.delete(attempts_key)
            return False, "Too many failed attempts. Please request a new code."

        # Verify code
        if stored_code != code:
            # Increment attempts
            new_attempts = await cache.incr(attempts_key)
            if new_attempts == 1:
                # Set TTL on first attempt
                await cache.expire(attempts_key, cls.ATTEMPTS_TTL)

            remaining = cls.MAX_ATTEMPTS - new_attempts
            return False, f"Invalid code. {remaining} attempts remaining."

        # Success - delete code (one-time use)
        await cache.delete(code_key)
        await cache.delete(attempts_key)

        return True, "Verification successful"

    @classmethod
    async def get_code_ttl(cls, email: str) -> int:
        """Get remaining TTL for verification code

        Returns:
            Remaining seconds, -2 if not exists
        """
        key = cls._get_key(cls.KEY_CODE, email)
        return await cache.ttl(key)

    @classmethod
    async def clear_all(cls, email: str):
        """Clear all verification data for email (useful for testing)"""
        email = email.lower().strip()
        await cache.delete(cls._get_key(cls.KEY_CODE, email))
        await cache.delete(cls._get_key(cls.KEY_SENT, email))
        await cache.delete(cls._get_key(cls.KEY_ATTEMPTS, email))
