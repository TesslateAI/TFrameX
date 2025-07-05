# TFrameX Architecture Diagrams

This document contains comprehensive architectural diagrams for the TFrameX framework, visualizing the core components, relationships, and execution flows.

## 1. Overall Framework Architecture

```mermaid
graph TD
    %% Core Application Layer
    A[TFrameXApp] --> B[TFrameXRuntimeContext]
    A --> C[Agent Registry]
    A --> D[Tool Registry]
    A --> E[Flow Registry]
    A --> F[MCP Manager]
    
    %% Runtime Context Components
    B --> G[Engine]
    B --> H[Memory Stores]
    B --> I[LLM Providers]
    
    %% Agent System
    C --> J[BaseAgent]
    J --> K[LLMAgent]
    J --> L[ToolAgent]
    
    %% Tool System
    D --> M[Native Tools]
    D --> N[MCP Tools]
    D --> O[Agent Tools]
    
    %% Flow System
    E --> P[Flow]
    E --> Q[Patterns]
    Q --> R[SequentialPattern]
    Q --> S[ParallelPattern]
    Q --> T[RouterPattern]
    Q --> U[DiscussionPattern]
    
    %% MCP Integration
    F --> V[MCP Servers]
    F --> W[Protocol Handlers]
    F --> X[Transport Layer]
    
    %% External Systems
    V --> Y[Stdio Servers]
    V --> Z[HTTP Servers]
    X --> AA[SSE Transport]
    X --> AB[HTTP Transport]
    
    %% Style Classes
    classDef core fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef agents fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef tools fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef flows fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef mcp fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    
    class A,B,G,H,I core
    class C,J,K,L agents
    class D,M,N,O tools
    class E,P,Q,R,S,T,U flows
    class F,V,W,X,Y,Z,AA,AB mcp
```

## 2. Core Component Architecture

```mermaid
graph LR
    %% Application Layer
    subgraph "Application Layer"
        A[TFrameXApp]
        B[TFrameXRuntimeContext]
        C[Engine]
    end
    
    %% Agent System
    subgraph "Agent System"
        D[BaseAgent]
        E[LLMAgent]
        F[ToolAgent]
        G[AgentFactory]
    end
    
    %% Tool System
    subgraph "Tool System"
        H[ToolRegistry]
        I[NativeTools]
        J[MCPTools]
        K[MetaTools]
        L[ToolSchema]
    end
    
    %% Flow System
    subgraph "Flow System"
        M[Flow]
        N[FlowContext]
        O[Patterns]
        P[FlowStep]
    end
    
    %% MCP Integration
    subgraph "MCP Integration"
        Q[MCPManager]
        R[ServerConnector]
        S[ProtocolHandler]
        T[TransportLayer]
    end
    
    %% Utilities
    subgraph "Utilities"
        U[LLMWrapper]
        V[MemoryStore]
        W[Logger]
        X[ConfigManager]
    end
    
    %% Relationships
    A --> B
    B --> C
    C --> D
    C --> H
    C --> M
    C --> Q
    
    D --> E
    D --> F
    C --> G
    
    H --> I
    H --> J
    H --> K
    H --> L
    
    M --> N
    M --> O
    M --> P
    
    Q --> R
    Q --> S
    Q --> T
    
    E --> U
    E --> V
    C --> W
    A --> X
    
    classDef app fill:#e3f2fd,stroke:#0d47a1,stroke-width:2px
    classDef agents fill:#f1f8e9,stroke:#33691e,stroke-width:2px
    classDef tools fill:#fff8e1,stroke:#f57f17,stroke-width:2px
    classDef flows fill:#fce4ec,stroke:#ad1457,stroke-width:2px
    classDef mcp fill:#e8eaf6,stroke:#283593,stroke-width:2px
    classDef utils fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
```

## 3. MCP Integration Architecture

```mermaid
graph TB
    %% MCP Manager
    subgraph "MCP Manager"
        A[MCPManager]
        B[Server Registry]
        C[Tool Aggregator]
        D[Capability Manager]
    end
    
    %% Server Connectors
    subgraph "Server Connectors"
        E[StdioConnector]
        F[HTTPConnector]
        G[SSEConnector]
    end
    
    %% Protocol Layer
    subgraph "Protocol Layer"
        H[Protocol Handler]
        I[Message Router]
        J[Notification Handler]
        K[Progress Tracker]
    end
    
    %% Transport Layer
    subgraph "Transport Layer"
        L[Stdio Transport]
        M[HTTP Transport]
        N[SSE Transport]
    end
    
    %% External MCP Servers
    subgraph "External MCP Servers"
        O[Math Server]
        P[SQLite Server]
        Q[Blender Server]
        R[AWS Docs Server]
        S[Custom Servers]
    end
    
    %% Capabilities
    subgraph "Advanced Capabilities"
        T[Roots Management]
        U[Sampling Control]
        V[Resource Access]
        W[Content Processing]
    end
    
    %% Data Flow
    A --> B
    A --> C
    A --> D
    
    B --> E
    B --> F
    B --> G
    
    E --> H
    F --> H
    G --> H
    
    H --> I
    H --> J
    H --> K
    
    I --> L
    I --> M
    I --> N
    
    L --> O
    M --> P
    M --> Q
    N --> R
    L --> S
    
    D --> T
    D --> U
    D --> V
    D --> W
    
    %% Style
    classDef manager fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef connector fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef protocol fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    classDef transport fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef servers fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef capabilities fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    
    class A,B,C,D manager
    class E,F,G connector
    class H,I,J,K protocol
    class L,M,N transport
    class O,P,Q,R,S servers
    class T,U,V,W capabilities
```

## 4. Agent Execution Flow

```mermaid
flowchart TD
    %% Input Processing
    A[User Input] --> B[Runtime Context]
    B --> C[Engine.execute_agent]
    
    %% Agent Resolution
    C --> D{Agent Type?}
    D -->|LLM Agent| E[LLMAgent.run]
    D -->|Tool Agent| F[ToolAgent.run]
    
    %% LLM Agent Flow
    E --> G[Load Memory]
    G --> H[Apply System Prompt]
    H --> I[Call LLM]
    I --> J{Tool Calls?}
    J -->|Yes| K[Execute Tools]
    J -->|No| L[Process Response]
    
    %% Tool Execution
    K --> M{Tool Type?}
    M -->|Native| N[Execute Native Tool]
    M -->|MCP| O[Execute MCP Tool]
    M -->|Agent| P[Execute Agent Tool]
    
    %% Tool Results
    N --> Q[Aggregate Results]
    O --> Q
    P --> Q
    Q --> R[Update Memory]
    R --> S{Continue?}
    S -->|Yes| I
    S -->|No| L
    
    %% Tool Agent Flow
    F --> T[Direct Tool Execution]
    T --> U[Return Result]
    
    %% Response Processing
    L --> V[Strip Think Tags]
    V --> W[Update Memory]
    W --> X[Return Response]
    U --> X
    
    %% Memory Management
    G --> Y[Memory Store]
    R --> Y
    W --> Y
    
    %% Style
    classDef input fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef execution fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef llm fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    classDef tools fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef memory fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef output fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    
    class A,B input
    class C,D execution
    class E,G,H,I,J,L,V llm
    class F,K,M,N,O,P,Q,T tools
    class R,S,W,Y memory
    class U,X output
```

## 5. Pattern Execution Flow

```mermaid
flowchart TD
    %% Pattern Entry
    A[Pattern.execute] --> B[FlowContext]
    B --> C{Pattern Type?}
    
    %% Sequential Pattern
    C -->|Sequential| D[SequentialPattern]
    D --> E[For Each Step]
    E --> F[Execute Agent]
    F --> G[Update Context]
    G --> H{More Steps?}
    H -->|Yes| E
    H -->|No| I[Return Context]
    
    %% Parallel Pattern
    C -->|Parallel| J[ParallelPattern]
    J --> K[Create Tasks]
    K --> L[Execute Concurrently]
    L --> M[Await All Results]
    M --> N[Aggregate Results]
    N --> O[Update Context]
    O --> I
    
    %% Router Pattern
    C -->|Router| P[RouterPattern]
    P --> Q[Execute Router Agent]
    Q --> R[Parse Route Decision]
    R --> S[Execute Selected Agent]
    S --> T[Update Context]
    T --> I
    
    %% Discussion Pattern
    C -->|Discussion| U[DiscussionPattern]
    U --> V[Initialize Round]
    V --> W[For Each Agent]
    W --> X[Execute Agent]
    X --> Y[Update Shared Context]
    Y --> Z{More Agents?}
    Z -->|Yes| W
    Z -->|No| AA{More Rounds?}
    AA -->|Yes| V
    AA -->|No| BB[Moderator Summary]
    BB --> I
    
    %% Nested Patterns
    F --> CC{Nested Pattern?}
    CC -->|Yes| C
    CC -->|No| G
    
    S --> DD{Nested Pattern?}
    DD -->|Yes| C
    DD -->|No| T
    
    X --> EE{Nested Pattern?}
    EE -->|Yes| C
    EE -->|No| Y
    
    %% Style
    classDef pattern fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef sequential fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef parallel fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    classDef router fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef discussion fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef context fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    
    class A,B,C pattern
    class D,E,F,G,H sequential
    class J,K,L,M,N,O parallel
    class P,Q,R,S,T router
    class U,V,W,X,Y,Z,AA,BB discussion
    class I,CC,DD,EE context
```

## 6. Configuration and Lifecycle

```mermaid
sequenceDiagram
    participant U as User
    participant A as TFrameXApp
    participant RC as RuntimeContext
    participant E as Engine
    participant MCP as MCPManager
    participant AG as Agent
    participant LLM as LLMWrapper
    participant MS as MemoryStore
    
    %% Initialization
    U->>A: Create App
    A->>A: Load Configuration
    A->>A: Register Agents/Tools
    A->>MCP: Initialize MCP Servers
    MCP-->>A: Servers Ready
    
    %% Runtime Context
    U->>A: run_context()
    A->>RC: Create Context
    RC->>E: Initialize Engine
    RC->>LLM: Initialize LLM
    RC->>MS: Initialize Memory
    
    %% Agent Execution
    U->>RC: Execute Agent
    RC->>E: execute_agent()
    E->>AG: Create/Get Agent
    AG->>MS: Load Memory
    AG->>LLM: Call LLM
    LLM-->>AG: Response
    AG->>MS: Save Memory
    AG-->>E: Result
    E-->>RC: Result
    RC-->>U: Response
    
    %% Tool Execution
    AG->>E: Execute Tool
    E->>MCP: Call MCP Tool
    MCP-->>E: Tool Result
    E-->>AG: Result
    
    %% Cleanup
    U->>RC: Exit Context
    RC->>MCP: Cleanup Servers
    RC->>MS: Cleanup Memory
    RC->>LLM: Cleanup LLM
    RC-->>A: Context Closed
```

## 7. Example Architecture: Website Designer

```mermaid
graph TB
    %% User Interface
    U[User Request] --> WC[WebsiteCoordinator]
    
    %% Coordinator Agent
    WC --> CS[ContentStrategist]
    WC --> HD[HTMLDeveloper]
    WC --> CD[CSSDesigner]
    WC --> UD[UIUXDesigner]
    
    %% Tools
    subgraph "File System Tools"
        FT[create_file]
        RT[read_file]
        LT[list_files]
        DT[delete_file]
    end
    
    %% Agent Tool Usage
    CS --> FT
    HD --> FT
    HD --> RT
    CD --> FT
    CD --> RT
    UD --> FT
    UD --> RT
    
    %% Parallel Execution
    subgraph "Parallel Development"
        HD --> HTML[HTML Files]
        CD --> CSS[CSS Files]
        UD --> UX[UX Assets]
    end
    
    %% File Outputs
    HTML --> WS[Website Files]
    CSS --> WS
    UX --> WS
    
    %% Review Process
    WS --> WC
    WC --> QA[Quality Assurance]
    QA --> WS
    
    %% Style
    classDef coordinator fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef agents fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef tools fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    classDef files fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef output fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    
    class WC,QA coordinator
    class CS,HD,CD,UD agents
    class FT,RT,LT,DT tools
    class HTML,CSS,UX files
    class WS output
```

## 8. Example Architecture: Content Creation Pipeline

```mermaid
flowchart LR
    %% Input
    A[Content Request] --> B[ContentStrategist]
    
    %% Strategy Phase
    B --> C[ContentResearcher]
    C --> D[ContentRouter]
    
    %% Routing Decision
    D --> E{Content Type?}
    E -->|Technical| F[TechnicalWriter]
    E -->|Marketing| G[MarketingWriter]
    E -->|Creative| H[CreativeWriter]
    E -->|News| I[NewsWriter]
    E -->|Business| J[BusinessWriter]
    
    %% Content Creation
    F --> K[SEOOptimizer]
    G --> K
    H --> K
    I --> K
    J --> K
    
    %% Quality Assurance
    K --> L[ContentEditor]
    L --> M[QualityAssurance]
    
    %% Analysis
    M --> N[ContentAnalyzer]
    N --> O{Quality OK?}
    O -->|No| P[RevisionAgent]
    P --> L
    O -->|Yes| Q[Final Content]
    
    %% Parallel Analysis
    M --> R[ParallelAnalyzer]
    R --> S[Technical Analysis]
    R --> T[Marketing Analysis]
    R --> U[Creative Analysis]
    
    S --> V[Analysis Report]
    T --> V
    U --> V
    
    %% Style
    classDef input fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef strategy fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef writers fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    classDef quality fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef analysis fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef output fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    
    class A input
    class B,C,D strategy
    class F,G,H,I,J writers
    class K,L,M,P quality
    class N,R,S,T,U,V analysis
    class Q output
```

## 9. Data Flow Architecture

```mermaid
graph LR
    %% Data Sources
    subgraph "Data Sources"
        A[User Input]
        B[Environment Variables]
        C[Configuration Files]
        D[MCP Servers]
        E[External APIs]
    end
    
    %% Processing Layer
    subgraph "Processing Layer"
        F[Input Validation]
        G[Context Assembly]
        H[Agent Execution]
        I[Tool Execution]
        J[Result Aggregation]
    end
    
    %% Storage Layer
    subgraph "Storage Layer"
        K[Memory Stores]
        L[Session Data]
        M[Configuration Cache]
        N[Tool Results]
    end
    
    %% Output Layer
    subgraph "Output Layer"
        O[Response Formatting]
        P[Logging]
        Q[Metrics]
        R[User Response]
    end
    
    %% Flow
    A --> F
    B --> G
    C --> G
    D --> I
    E --> I
    
    F --> G
    G --> H
    H --> I
    I --> J
    
    H --> K
    I --> N
    G --> M
    H --> L
    
    J --> O
    J --> P
    J --> Q
    O --> R
    
    %% Style
    classDef sources fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef processing fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef storage fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    classDef output fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    
    class A,B,C,D,E sources
    class F,G,H,I,J processing
    class K,L,M,N storage
    class O,P,Q,R output
```

## 10. Security and Compliance Architecture

```mermaid
graph TB
    %% Security Layers
    subgraph "Input Security"
        A[Input Validation]
        B[Parameter Sanitization]
        C[Schema Validation]
    end
    
    subgraph "Authentication & Authorization"
        D[API Key Management]
        E[Server Authentication]
        F[Resource Access Control]
    end
    
    subgraph "Execution Security"
        G[Sandbox Execution]
        H[Timeout Controls]
        I[Resource Limits]
    end
    
    subgraph "Data Security"
        J[Memory Isolation]
        K[Secure Storage]
        L[Data Encryption]
    end
    
    subgraph "Audit & Monitoring"
        M[Audit Logging]
        N[Security Metrics]
        O[Compliance Reporting]
    end
    
    %% Compliance Features
    subgraph "Compliance Features"
        P[HIPAA Compliance]
        Q[Data Retention]
        R[Privacy Controls]
    end
    
    %% Relationships
    A --> D
    B --> E
    C --> F
    
    D --> G
    E --> H
    F --> I
    
    G --> J
    H --> K
    I --> L
    
    J --> M
    K --> N
    L --> O
    
    M --> P
    N --> Q
    O --> R
    
    %% Style
    classDef input fill:#ffebee,stroke:#d32f2f,stroke-width:2px
    classDef auth fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef exec fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef data fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    classDef audit fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef compliance fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    
    class A,B,C input
    class D,E,F auth
    class G,H,I exec
    class J,K,L data
    class M,N,O audit
    class P,Q,R compliance
```

---

These comprehensive architectural diagrams provide a complete visual representation of the TFrameX framework, from high-level architecture to detailed execution flows and example implementations. Each diagram focuses on different aspects of the system, making it easy to understand the framework's design and implementation patterns.