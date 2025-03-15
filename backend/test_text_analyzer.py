import asyncio
from text_analyzer import process_thinking_text

SAMPLE_TEXT = """
I need to decide how to implement the authentication system for our web application.

First, I'll consider the available options:
1. Use JWT (JSON Web Tokens)
2. Use session-based authentication
3. Use OAuth with a third-party provider

For JWT:
- Pros: Stateless, scalable, works well with microservices
- Cons: Token size can be large, revocation is challenging

For session-based:
- Pros: Simple to implement, easier to revoke
- Cons: Requires server-side storage, doesn't scale as well

For OAuth:
- Pros: Delegates authentication, users don't need new credentials
- Cons: Dependency on third-party, more complex implementation

After considering the requirements of our application, I've decided to go with JWT authentication because:
1. We're building a distributed system with multiple services
2. We need stateless authentication for horizontal scaling
3. The token expiration time can be short, mitigating revocation issues

Next, I need to decide on the JWT signing algorithm:
- HS256 (HMAC with SHA-256)
- RS256 (RSA Signature with SHA-256)

For HS256:
- Pros: Simple, fast
- Cons: Same key for signing and verification

For RS256:
- Pros: Different keys for signing and verification
- Cons: More complex, slower

I'll choose RS256 because we need to verify tokens across multiple services without sharing the signing key.

Now I'll implement the JWT authentication middleware using the jsonwebtoken library.
"""


async def main():
    print("Processing thinking text...")
    function_calls = await process_thinking_text(SAMPLE_TEXT)

    print("\nGenerated function calls:")
    for i, call in enumerate(function_calls, 1):
        print(f"\n{i}. Function: {call['name']}")
        print(f"   Arguments: {call['args']}")


if __name__ == "__main__":
    asyncio.run(main())
