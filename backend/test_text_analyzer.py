import asyncio
from text_analyzer import (
    IncrementalTextAnalyzer,
    SyncIncrementalTextAnalyzer,
)

SAMPLE_TEXT = """
I need to design and implement a complete architecture for our new e-commerce platform.

STEP 1: REQUIREMENTS ANALYSIS
First, I'll identify the key requirements:
- High scalability to handle seasonal traffic spikes
- Secure payment processing
- Personalized user experience
- Mobile-friendly interface
- Inventory management integration
- Analytics capabilities
- Fast search functionality

STEP 2: ARCHITECTURE DECISION
I need to decide on the overall architecture approach:

Option 1: Monolithic Architecture
- Pros: Simpler development, easier deployment initially
- Cons: Harder to scale, tightly coupled components, single point of failure

Option 2: Microservices Architecture
- Pros: Independent scaling, technology diversity, fault isolation
- Cons: Increased complexity, distributed system challenges, more operational overhead

Option 3: Serverless Architecture
- Pros: No server management, auto-scaling, pay-per-use
- Cons: Vendor lock-in, cold starts, limited execution time

After careful consideration, I'll choose Microservices Architecture because:
1. We anticipate rapid growth and need independent scaling
2. Different teams can work on different services
3. We can deploy updates to individual services without affecting the entire system
4. Better fault isolation for critical components like payment processing

STEP 3: DATABASE SELECTION
Now I need to choose the right database solution:

Option 1: Traditional RDBMS (PostgreSQL)
- Pros: ACID compliance, mature technology, good for structured data
- Cons: Scaling challenges, schema rigidity

Option 2: NoSQL Document Store (MongoDB)
- Pros: Schema flexibility, horizontal scaling, good for semi-structured data
- Cons: Eventual consistency, less mature than RDBMS

Option 3: Multi-model Database (FaunaDB)
- Pros: Combines relational and document models, global distribution
- Cons: Newer technology, smaller community

Option 4: Polyglot Persistence (multiple databases)
- Pros: Best tool for each job, specialized optimization
- Cons: Increased complexity, data synchronization challenges

I initially think MongoDB would be best because of its flexibility and scaling capabilities.

Wait, I need to reconsider. Our e-commerce platform will have many relational data requirements (orders, products, customers) where ACID transactions are important.

Let me go with Option 4: Polyglot Persistence:
- PostgreSQL for transactional data (orders, payments, inventory)
- MongoDB for product catalog and user profiles
- Redis for caching and session management
- Elasticsearch for search functionality

This approach gives us the benefits of each database type while minimizing the drawbacks.

STEP 4: FRONTEND FRAMEWORK SELECTION
For the frontend, I need to choose a framework:

Option 1: React
- Pros: Large ecosystem, component-based, virtual DOM
- Cons: Requires additional libraries for routing, state management

Option 2: Angular
- Pros: Complete solution, TypeScript integration, two-way binding
- Cons: Steeper learning curve, more opinionated

Option 3: Vue.js
- Pros: Gentle learning curve, flexible, good documentation
- Cons: Smaller ecosystem than React, fewer enterprise adoptions

Option 4: Next.js (React-based)
- Pros: Server-side rendering, static site generation, built-in routing
- Cons: Adds complexity, may be overkill for simpler applications

I'll choose Next.js because:
1. Server-side rendering will improve SEO and initial load performance
2. Built-in routing simplifies development
3. Static site generation for product pages will improve performance
4. React ecosystem availability while solving common React limitations

STEP 5: AUTHENTICATION SYSTEM
Now I need to decide on the authentication system:

Option 1: JWT (JSON Web Tokens)
- Pros: Stateless, scalable, works well with microservices
- Cons: Token size can be large, revocation is challenging

Option 2: Session-based authentication
- Pros: Simple to implement, easier to revoke
- Cons: Requires server-side storage, doesn't scale as well

Option 3: OAuth with a third-party provider
- Pros: Delegates authentication, users don't need new credentials
- Cons: Dependency on third-party, more complex implementation

Option 4: Custom authentication service
- Pros: Complete control, tailored to our needs
- Cons: Security risks if not implemented correctly, maintenance burden

I'll implement a hybrid approach:
- OAuth for social login (Google, Facebook, Apple)
- JWT for API authentication between services
- Redis to maintain a token blacklist for revocation

This gives us the benefits of JWT for our microservices while addressing the revocation issue.

STEP 6: PAYMENT PROCESSING
For payment processing, I need to evaluate:

Option 1: Stripe
- Pros: Developer-friendly, extensive documentation, handles compliance
- Cons: Transaction fees, limited customization

Option 2: PayPal
- Pros: Widely recognized, built-in user base, multiple payment methods
- Cons: Higher fees for some transactions, less modern API

Option 3: Braintree
- Pros: Owned by PayPal but with better API, multiple payment methods
- Cons: Less market penetration than PayPal or Stripe

Option 4: Custom payment integration with multiple providers
- Pros: Maximum flexibility, potential for lower fees
- Cons: PCI compliance burden, significant development effort

I'll choose Stripe as our primary payment processor because:
1. Developer-friendly API will speed up implementation
2. Handles PCI compliance
3. Supports multiple payment methods
4. Webhook system integrates well with our microservices

However, I'll design the payment service with an abstraction layer to make it easier to add additional payment providers in the future.

STEP 7: DEPLOYMENT STRATEGY
For deployment, I need to decide on:

Option 1: Traditional VMs
- Pros: Familiar, full control, potentially lower cost for stable workloads
- Cons: Manual scaling, less efficient resource utilization

Option 2: Kubernetes
- Pros: Container orchestration, automated scaling, service discovery
- Cons: Complexity, learning curve, operational overhead

Option 3: Managed Kubernetes (EKS, GKE, AKS)
- Pros: Reduced operational burden, managed control plane
- Cons: Higher cost than self-managed, still complex

Option 4: Platform as a Service (Heroku, Google App Engine)
- Pros: Simplicity, focus on code not infrastructure
- Cons: Less control, potential vendor lock-in, can be expensive at scale

I initially think Kubernetes would be best for our microservices architecture.

After discussing with the operations team, I realize we don't have enough Kubernetes expertise yet. Let's reconsider.

I'll choose Option 3: Managed Kubernetes (specifically GKE) because:
1. Aligns well with microservices architecture
2. Reduces operational burden compared to self-managed Kubernetes
3. Google's managed service has good reliability and feature set
4. We can gradually build Kubernetes expertise while Google manages the control plane

STEP 8: SEARCH FUNCTIONALITY
For product search, I need to evaluate:

Option 1: Database queries (PostgreSQL full-text search)
- Pros: Integrated with existing database, no additional system
- Cons: Limited advanced features, performance issues at scale

Option 2: Elasticsearch
- Pros: Powerful full-text search, faceting, analytics capabilities
- Cons: Additional system to maintain, eventual consistency

Option 3: Algolia
- Pros: Managed service, excellent performance, easy implementation
- Cons: Ongoing costs, less control

Option 4: Custom search implementation
- Pros: Tailored to our specific needs, potentially lower cost
- Cons: Development effort, maintenance burden

I'll choose Elasticsearch because:
1. Powerful search capabilities including faceted search and typo tolerance
2. Can scale independently from our primary databases
3. Useful for both product search and analytics
4. Open-source with option to move to managed Elastic Cloud if needed

STEP 9: CACHING STRATEGY
For caching, I need to decide on:

Option 1: Application-level caching (in-memory)
- Pros: Simple, no additional systems
- Cons: Not shared across instances, memory limitations

Option 2: Redis
- Pros: Fast, versatile (can be used for more than caching), mature
- Cons: Another system to maintain

Option 3: CDN caching
- Pros: Globally distributed, handles static assets well
- Cons: Limited for dynamic content

Option 4: Multi-level caching strategy
- Pros: Optimized for different types of data and access patterns
- Cons: Increased complexity, potential for stale data

I'll implement a multi-level caching strategy:
- CDN (Cloudflare) for static assets and product images
- Redis for session data, API responses, and frequently accessed data
- Browser caching for appropriate assets
- HTTP caching headers for API responses

This comprehensive approach will minimize database load and improve user experience.

STEP 10: MESSAGING SYSTEM
For communication between microservices, I need to choose:

Option 1: REST API calls
- Pros: Simple, widely understood, synchronous
- Cons: Tight coupling, potential performance issues

Option 2: gRPC
- Pros: Efficient binary protocol, strong typing with protobuf
- Cons: Less human-readable, requires more setup

Option 3: Message queue (RabbitMQ)
- Pros: Decoupling, reliable delivery, patterns like pub/sub
- Cons: Additional system, potential message ordering issues

Option 4: Event streaming (Kafka)
- Pros: Event sourcing capability, replay ability, high throughput
- Cons: Complex, higher resource requirements

I initially think RabbitMQ would be sufficient for our needs.

After further consideration of our requirements, I realize we need event sourcing capabilities for order processing and inventory management.

I'll choose Kafka because:
1. Provides event sourcing capabilities for critical business events
2. Allows for replay of events for new services or recovery
3. High throughput for handling peak traffic periods
4. Enables real-time analytics and monitoring

STEP 11: LOGGING AND MONITORING
For observability, I need to decide on:

Option 1: ELK Stack (Elasticsearch, Logstash, Kibana)
- Pros: Powerful search, visualization, open-source
- Cons: Resource intensive, requires maintenance

Option 2: Prometheus + Grafana
- Pros: Great for metrics, alerting, open-source
- Cons: Not primarily for logs, requires additional components

Option 3: Cloud provider solutions (CloudWatch, Stackdriver)
- Pros: Integrated with cloud platform, managed service
- Cons: Potential vendor lock-in, can be expensive at scale

Option 4: Third-party SaaS (Datadog, New Relic)
- Pros: Comprehensive features, managed service
- Cons: Ongoing costs, potential data privacy concerns

I'll implement a hybrid approach:
- Prometheus + Grafana for metrics and alerting
- ELK stack for log aggregation and analysis
- Distributed tracing with Jaeger
- Custom health check endpoints for each service

This comprehensive observability solution will help us identify and resolve issues quickly.

STEP 12: SECURITY IMPLEMENTATION
For security, I need to address:

Option 1: Basic security measures
- Pros: Simpler implementation, lower initial effort
- Cons: May miss important protections, higher risk

Option 2: Comprehensive security framework
- Pros: Systematic approach, better coverage
- Cons: Higher implementation effort, potential performance impact

Option 3: Third-party security services
- Pros: Expertise from security specialists, managed services
- Cons: Ongoing costs, integration challenges

I'll implement a comprehensive security approach:
- HTTPS everywhere with automatic certificate management
- WAF (Web Application Firewall) for common attack protection
- Rate limiting for API endpoints
- Input validation and output encoding
- Regular security audits and penetration testing
- Secret management with HashiCorp Vault
- Network segmentation in Kubernetes

This multi-layered approach will provide defense in depth.

STEP 13: CI/CD PIPELINE
For continuous integration and deployment, I need to choose:

Option 1: Jenkins
- Pros: Highly customizable, extensive plugin ecosystem
- Cons: Requires maintenance, can be complex to set up

Option 2: GitLab CI
- Pros: Integrated with GitLab, container-native
- Cons: Less flexible than Jenkins, potential vendor lock-in

Option 3: GitHub Actions
- Pros: Integrated with GitHub, easy to set up
- Cons: Relatively new, potential limitations for complex workflows

Option 4: Cloud-native CI/CD (Cloud Build, CodePipeline)
- Pros: Integrated with cloud platform, managed service
- Cons: Potential vendor lock-in, platform-specific

I'll choose GitHub Actions because:
1. We already use GitHub for source control
2. Easy to set up and maintain
3. Good integration with Kubernetes
4. Sufficient flexibility for our deployment needs

STEP 14: FINAL ARCHITECTURE REVIEW
After making all these decisions, I need to review the complete architecture:

- Microservices architecture deployed on GKE
- Polyglot persistence with PostgreSQL, MongoDB, Redis, and Elasticsearch
- Next.js frontend with server-side rendering
- Hybrid authentication with OAuth and JWT
- Stripe for payment processing
- Multi-level caching strategy
- Kafka for event streaming and service communication
- Comprehensive observability with Prometheus, Grafana, and ELK
- Multi-layered security approach
- GitHub Actions for CI/CD

This architecture addresses all our requirements and provides a solid foundation for our e-commerce platform. It balances modern technology choices with practical considerations for development and operations.

Now I'll start implementing the core services, beginning with the product catalog and user authentication.
"""


async def test_incremental_analyzer():
    """
    Test the incremental text analyzer with chunks of text.
    """
    print("\n=== TESTING INCREMENTAL TEXT ANALYZER ===\n")

    # Create an incremental text analyzer
    analyzer = IncrementalTextAnalyzer(session_id="test_session")
    await analyzer.initialize()

    # Split the sample text into chunks
    chunks = SAMPLE_TEXT.split("\n\n")

    # Process each chunk incrementally
    for i, chunk in enumerate(chunks):
        if i > 5:  # Limit to first few chunks for demonstration
            break

        print(f"\n--- Processing Chunk {i+1} ---")
        print(
            f"Chunk content: {chunk[:100]}..."
            if len(chunk) > 100
            else f"Chunk content: {chunk}"
        )

        # Add the chunk to the analyzer
        function_calls = await analyzer.add_text_chunk(chunk + "\n\n")

        # Print the function calls that were executed
        print(f"Function calls executed: {len(function_calls)}")
        for call in function_calls:
            print(f"  - {call['name']}: {call['args']}")

    print("\n=== INCREMENTAL ANALYZER TEST COMPLETE ===\n")


def test_sync_incremental_analyzer():
    """
    Test the synchronous incremental text analyzer with chunks of text.
    """
    print("\n=== TESTING SYNCHRONOUS INCREMENTAL TEXT ANALYZER ===\n")

    # Create a synchronous incremental text analyzer
    analyzer = SyncIncrementalTextAnalyzer(session_id="test_sync_session")

    # Split the sample text into chunks
    chunks = SAMPLE_TEXT.split("\n\n")

    # Process each chunk incrementally
    for i, chunk in enumerate(chunks):

        print(f"\n--- Processing Chunk {i+1} ---")
        print(
            f"Chunk content: {chunk[:100]}..."
            if len(chunk) > 100
            else f"Chunk content: {chunk}"
        )

        try:
            # Add the chunk to the analyzer
            function_calls = analyzer.add_text_chunk(chunk + "\n\n")

            # Print the function calls that were executed
            print(f"Function calls executed: {len(function_calls)}")
            for call in function_calls:
                print(f"  - {call['name']}: {call['args']}")
        except Exception as e:
            print(f"Error processing chunk: {str(e)}")
            # Continue with the next chunk

    print("\n=== SYNCHRONOUS INCREMENTAL ANALYZER TEST COMPLETE ===\n")


async def main():
    """
    Main function to run the tests.
    """

    await test_incremental_analyzer()

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            print("\nSkipping synchronous test in running event loop")
        else:
            test_sync_incremental_analyzer()
    except RuntimeError:
        test_sync_incremental_analyzer()


if __name__ == "__main__":
    asyncio.run(main())
