# 🤖 RoboShop Microservices on Kubernetes

## 📚 Table of Contents
- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Core Kubernetes Concepts](#core-kubernetes-concepts)
- [Microservices Components](#microservices-components)
- [Configuration Management](#configuration-management)
- [Resource Management](#resource-management)
- [Networking & Service Discovery](#networking--service-discovery)
- [Docker Best Practices](#docker-best-practices)
- [Deployment Strategies](#deployment-strategies)
- [Troubleshooting Guide](#troubleshooting-guide)
- [Production Best Practices](#production-best-practices)

---

## 🎯 Project Overview

**RoboShop** is a full-stack e-commerce application demonstrating microservices architecture deployed on Kubernetes. It consists of multiple services written in different programming languages, showcasing polyglot architecture.

### Technology Stack
- **Frontend**: Nginx (Web Server)
- **Backend Services**: Node.js (Cart, Catalogue, User), Java (Shipping), Python (Payment)
- **Databases**: MongoDB, MySQL, Redis
- **Message Queue**: RabbitMQ
- **Orchestration**: Kubernetes

---

## 🏗️ Architecture

### Microservices Communication Flow

```
┌─────────────┐
│  Web (Nginx)│ ──┐
└─────────────┘   │
                  │
     ┌────────────┼────────────┬──────────┬──────────┐
     │            │            │          │          │
     ▼            ▼            ▼          ▼          ▼
┌─────────┐  ┌────────┐  ┌────────┐ ┌─────────┐ ┌─────────┐
│Catalogue│  │  Cart  │  │  User  │ │Shipping │ │ Payment │
└─────────┘  └────────┘  └────────┘ └─────────┘ └─────────┘
     │            │           │          │           │
     ▼            ▼           ▼          ▼           ▼
┌─────────┐  ┌────────┐  ┌────────┐ ┌─────────┐ ┌─────────┐
│ MongoDB │  │ Redis  │  │ Redis  │ │  MySQL  │ │RabbitMQ │
└─────────┘  └────────┘  │ MongoDB│ └─────────┘ └─────────┘
                         └────────┘
```

### Service Dependencies
- **Web** → Catalogue, Cart, User, Shipping
- **Cart** → Redis, Catalogue
- **Catalogue** → MongoDB
- **User** → MongoDB, Redis
- **Shipping** → MySQL, Cart
- **Payment** → RabbitMQ, Cart, User

---

## 📖 Core Kubernetes Concepts

### 1. Namespaces
**Purpose**: Logical isolation of resources within a cluster

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: roboshop
```

**Key Concepts**:
- Provides scope for names (resource names must be unique within a namespace)
- Enables resource quotas and access control
- Default namespaces: `default`, `kube-system`, `kube-public`, `kube-node-lease`

**Best Practices**:
- Use namespaces to separate environments (dev, staging, prod)
- Apply resource quotas per namespace
- Use RBAC for namespace-level access control
- Never use `default` namespace for applications

---

### 2. Pods
**Definition**: Smallest deployable unit in Kubernetes; one or more containers that share network and storage

**Key Characteristics**:
- Ephemeral by nature (can be created/destroyed dynamically)
- Share the same network namespace (localhost communication)
- Share storage volumes
- Single IP address per pod

**Lifecycle Phases**:
1. **Pending**: Accepted by cluster but not yet running
2. **Running**: Bound to node and at least one container is running
3. **Succeeded**: All containers terminated successfully
4. **Failed**: At least one container failed
5. **Unknown**: State cannot be determined

---

### 3. Deployments
**Purpose**: Declarative updates for Pods and ReplicaSets

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: catalogue
  namespace: roboshop
  labels:
    app: catalogue
    tier: app
    project: roboshop
spec:
  replicas: 1
  selector:
    matchLabels:
      app: catalogue
      tier: app
      project: roboshop
  template:
    metadata:
      labels:
        app: catalogue
        tier: app
        project: roboshop
    spec:
      containers:
      - name: catalogue
        image: sarthak6700/catalogue:v1
```

**Key Features**:
- **Rolling Updates**: Zero-downtime deployments
- **Rollbacks**: Revert to previous versions
- **Scaling**: Horizontal scaling via replica count
- **Self-healing**: Automatically replaces failed pods

**Important Fields Explained**:

#### `metadata.labels`
- Attached to the Deployment object itself
- Used for organizing and filtering Deployments
- Example: "This Deployment belongs to roboshop project, web tier"

#### `spec.selector.matchLabels`
- **Critical**: Defines which Pods this Deployment manages
- Must match `template.metadata.labels`
- Selector = "Which Pods are mine?"
- Deployment can only manage Pods with ALL these labels

#### `template.metadata.labels`
- Labels assigned to every Pod created by this Deployment
- Template = "What Pods do I create?"
- These labels must match `spec.selector.matchLabels`

**Label Hierarchy**:
```
Deployment Labels (metadata.labels)
    │
    ├─ For Deployment Organization
    │
    └─ selector.matchLabels ─── Must Match ──→ template.metadata.labels
                                                      │
                                                      └─ Labels on Pods
```

---

### 4. Services
**Purpose**: Stable network endpoint to access Pods

**Service Types**:

#### ClusterIP (Default)
```yaml
apiVersion: v1
kind: Service
metadata:
  name: catalogue
  namespace: roboshop
spec:
  type: ClusterIP
  selector:
    app: catalogue
    tier: app
    project: roboshop
  ports:
  - name: catalogue-port
    protocol: TCP
    port: 8080        # Service port (internal cluster access)
    targetPort: 8080  # Container port
```

- **Use Case**: Internal service-to-service communication
- **Access**: Only within cluster
- **Example**: Database services, internal APIs

#### NodePort
```yaml
spec:
  type: NodePort
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080  # Optional: 30000-32767 range
```

- **Use Case**: External access during development
- **Access**: `<NodeIP>:<NodePort>`
- **Range**: 30000-32767

#### LoadBalancer
```yaml
spec:
  type: LoadBalancer
```

- **Use Case**: Production external access
- **Requirement**: Cloud provider integration (AWS ELB, GCP LB, Azure LB)
- **Behavior**: Creates external load balancer automatically

**Port Terminology**:
- **port**: Service's port (how other services talk to this service)
- **targetPort**: Container's port (where application listens)
- **nodePort**: External port on node (only for NodePort type)

---

### 5. ConfigMaps
**Purpose**: Store non-confidential configuration data

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: catalogue
  namespace: roboshop
data:
  MONGO: "true"
  MONGO_URL: "mongodb://mongodb:27017/catalogue"
```

**Usage in Pods**:
```yaml
containers:
- name: catalogue
  envFrom:
  - configMapRef:
      name: catalogue
```

**Best Practices**:
- Store configuration separate from code
- Use for environment-specific settings
- Never store sensitive data (use Secrets instead)
- Update ConfigMaps without rebuilding images
- Version your ConfigMaps for rollback capability

**Alternative Usage Patterns**:
```yaml
# As individual environment variables
env:
- name: MONGO_URL
  valueFrom:
    configMapKeyRef:
      name: catalogue
      key: MONGO_URL

# As volume mount
volumes:
- name: config
  configMap:
    name: nginx-conf
```

---

### 6. Secrets
**Purpose**: Store sensitive information (passwords, tokens, keys)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mysql-secret
  namespace: roboshop
type: Opaque
data:
  password: Um9ib1Nob3BAMQo=  # base64 encoded
```

**Best Practices**:
- Always use Secrets for sensitive data
- Enable encryption at rest
- Use external secret management (HashiCorp Vault, AWS Secrets Manager)
- Limit access via RBAC
- Rotate secrets regularly
- Never commit secrets to Git

---

## 🔧 Microservices Components

### Web (Frontend)

**Technology**: Nginx

**Purpose**: 
- Serves static content (HTML, CSS, JS, images)
- Acts as reverse proxy to backend services
- Handles routing to microservices

**Key Configuration**:
```nginx
location /api/catalogue/ {
  proxy_pass http://catalogue:8080/;
}
```

**Docker Strategy**:
```dockerfile
FROM nginx
RUN rm -rf /usr/share/nginx/html/index.html
COPY roboshop.conf /etc/nginx/nginx.conf
ADD static /usr/share/nginx/html/
```

**ConfigMap Integration**:
- Nginx configuration stored in ConfigMap
- Mounted as volume at `/etc/nginx/nginx.conf`
- Allows configuration updates without rebuilding image

---

### Catalogue Service

**Technology**: Node.js + MongoDB

**Responsibility**: Product catalog management

**Database Schema**:
- Products collection with fields: sku, name, description, price, instock, categories

**Key Features**:
- Text search on products
- Category filtering
- Product lookup by SKU

**Connection Pattern**:
```javascript
var mongoURL = process.env.MONGO_URL || 'mongodb://mongodb:27017/catalogue';
mongoClient.connect(mongoURL, (error, client) => {
  // Connection logic
});
```

**Retry Logic**: Implements exponential backoff for database connections

---

### Cart Service

**Technology**: Node.js + Redis

**Responsibility**: Shopping cart management

**Key Operations**:
- Add items to cart
- Update quantities
- Calculate totals and tax
- Merge cart on login
- Add shipping costs

**Redis Usage**:
```javascript
redisClient.setex(id, 3600, JSON.stringify(cart), callback);
```

**Data Structure**:
```json
{
  "total": 1000,
  "tax": 166.67,
  "items": [
    {
      "qty": 1,
      "sku": "ROB-1",
      "name": "Robbie",
      "price": 1200,
      "subtotal": 1200
    }
  ]
}
```

**Dependencies**: Communicates with Catalogue service for product validation

---

### User Service

**Technology**: Node.js + MongoDB + Redis

**Responsibility**: User authentication and order history

**Key Features**:
- User registration
- Login authentication
- Anonymous user tracking (via Redis INCR)
- Order history management

**Dual Database Usage**:
- **MongoDB**: User data and order history
- **Redis**: Anonymous user counter

---

### Shipping Service

**Technology**: Java (Spring Boot) + MySQL

**Responsibility**: Shipping calculation and order processing

**Build Process**: Multi-stage Docker build
```dockerfile
FROM maven AS build
# Build stage
FROM eclipse-temurin:8-jre-alpine
# Runtime stage
```

**Benefits of Multi-stage**:
- Smaller final image (JRE vs JDK)
- Build tools not included in production image
- Improved security

---

### Payment Service

**Technology**: Python (Flask/uWSGI) + RabbitMQ

**Responsibility**: Payment processing

**Message Queue Integration**: Uses RabbitMQ for asynchronous payment processing

**Docker Setup**:
```dockerfile
FROM python:3.9-alpine
RUN pip install -r requirements.txt
CMD ["uwsgi", "--ini", "payment.ini"]
```

---

### MongoDB

**Purpose**: Primary database for Catalogue and User services

**Initialization**: Uses init scripts
```dockerfile
COPY *.js /docker-entrypoint-initdb.d/
```

**Init Scripts**:
- `catalogue.js`: Seeds product data, creates indexes
- `user.js`: Seeds user data

**Index Types**:
```javascript
// Text index for search
db.products.createIndex({
  name: "text",
  description: "text"
});

// Unique index
db.products.createIndex({ sku: 1 }, { unique: true });
```

---

### MySQL

**Purpose**: Database for Shipping service

**Configuration**: Uses ConfigMap for environment variables
```yaml
data:
  MYSQL_ALLOW_EMPTY_PASSWORD: "yes"
  MYSQL_DATABASE: "cities"
  MYSQL_USER: "shipping"
  MYSQL_PASSWORD: "RoboShop@1"
```

**Init Process**: SQL scripts in `/docker-entrypoint-initdb.d/`

---

### Redis

**Purpose**: 
- Cart data storage (with TTL)
- User session management
- Anonymous user tracking

**Deployment**: Standard Redis image with resource limits

**Key Features**:
- In-memory data store
- Persistence optional
- Automatic expiration (TTL)

---

### RabbitMQ

**Purpose**: Message queue for asynchronous processing

**Use Case**: Payment service publishes order events

**Standard Port**: 5672

---

## ⚙️ Configuration Management

### Environment Variables Best Practices

**1. Hierarchy of Configuration**:
```
Hardcoded Defaults (in code)
    ↓
ConfigMap (environment-specific)
    ↓
Secrets (sensitive data)
    ↓
Command-line args or env overrides
```

**2. Naming Conventions**:
- Use UPPERCASE_WITH_UNDERSCORES
- Group related configs with prefixes (DB_HOST, DB_PORT)
- Be explicit (CATALOGUE_HOST not just HOST)

**3. Service Discovery Pattern**:
```javascript
var catalogueHost = process.env.CATALOGUE_HOST || 'catalogue'
var cataloguePort = process.env.CATALOGUE_PORT || '8080'
```

**4. Connection Strings**:
```yaml
MONGO_URL: "mongodb://mongodb:27017/catalogue"
# protocol://service-name:service-port/database
```

---

## 📊 Resource Management

### CPU and Memory Requests/Limits

```yaml
resources:
  requests:        # Minimum guaranteed resources
    cpu: "50m"     # 50 millicores (0.05 CPU)
    memory: "68Mi" # 68 Mebibytes
  limits:          # Maximum allowed resources
    cpu: "100m"
    memory: "128Mi"
```

**Understanding Resource Units**:

**CPU**:
- `1` = 1 full CPU core
- `100m` = 0.1 CPU (10% of one core)
- `1000m` = 1 CPU

**Memory**:
- `Mi` = Mebibyte (1024² bytes)
- `Gi` = Gibibyte (1024³ bytes)
- `M` = Megabyte (1000² bytes)

**Requests vs Limits**:
- **Requests**: Used for scheduling (pod placement)
- **Limits**: Enforced by kubelet (CPU throttled, memory killed)

**Best Practices**:
- Set requests based on average usage
- Set limits at 1.5-2x requests
- Monitor actual usage and adjust
- Database pods need higher memory
- Stateless services can have lower resources

---

### Horizontal Pod Autoscaling (HPA)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: catalogue
  namespace: roboshop
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: catalogue
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 75
```

**How It Works**:
1. Metrics server collects resource usage
2. HPA controller checks every 15 seconds (default)
3. If average CPU > 75%, scale up
4. If average CPU < target, scale down

**Prerequisites**:
- Metrics Server installed
- Resource requests defined
- Application must be horizontally scalable

---

## 🌐 Networking & Service Discovery

### DNS in Kubernetes

**Within Same Namespace**:
```
service-name
# Example: http://catalogue:8080
```

**Across Namespaces**:
```
service-name.namespace.svc.cluster.local
# Example: http://catalogue.roboshop.svc.cluster.local:8080
```

**DNS Resolution Components**:
- CoreDNS: Cluster DNS server
- Each pod gets DNS resolver configured automatically
- Service name resolves to ClusterIP

---

### Service Discovery Pattern

```javascript
// Application code
const catalogueHost = process.env.CATALOGUE_HOST || 'catalogue';
const cataloguePort = process.env.CATALOGUE_PORT || '8080';
const url = `http://${catalogueHost}:${cataloguePort}/product/${sku}`;
```

**Benefits**:
- No hardcoded IPs
- Services can be replaced without code changes
- Automatic load balancing
- Works across namespaces

---

### Network Policies (Advanced)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: catalogue-netpol
spec:
  podSelector:
    matchLabels:
      app: catalogue
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: web
```

**Use Cases**:
- Restrict traffic between microservices
- Implement zero-trust security
- Prevent lateral movement

---

## 🐳 Docker Best Practices

### Multi-Stage Builds

```dockerfile
# Stage 1: Build
FROM maven AS build
WORKDIR /opt/shipping
COPY pom.xml .
RUN mvn dependency:resolve
COPY src ./src
RUN mvn package

# Stage 2: Runtime
FROM eclipse-temurin:8-jre-alpine
WORKDIR /opt/shipping
COPY --from=build /opt/shipping/target/shipping-1.0.jar shipping.jar
CMD ["java", "-jar", "shipping.jar"]
```

**Benefits**:
- **Smaller Images**: 800MB → 150MB
- **Security**: No build tools in production
- **Faster Deployments**: Less data to transfer

---

### Image Tagging Strategy

**Bad Practice**:
```yaml
image: myapp:latest
```

**Good Practice**:
```yaml
image: sarthak6700/catalogue:v1.2.3
```

**Recommended Strategies**:
1. **Semantic Versioning**: `v1.2.3`
2. **Git SHA**: `abc123f`
3. **Build Number**: `build-456`
4. **Date-based**: `2025-01-03`

**Never use**:
- `latest` in production
- Mutable tags

---

### Dockerfile Optimization

```dockerfile
# ✅ Good: Layer caching
FROM node:14
WORKDIR /opt/server
COPY package.json .     # Copy dependencies first
RUN npm install         # This layer is cached
COPY server.js .        # Copy code last

# ❌ Bad: No caching
FROM node:14
WORKDIR /opt/server
COPY . .               # Everything copied together
RUN npm install        # Reinstalls on every code change
```

**Optimization Tips**:
1. Order Dockerfile instructions from least to most frequently changing
2. Use `.dockerignore` file
3. Combine RUN commands to reduce layers
4. Use specific base image tags
5. Run as non-root user

---

## 🚀 Deployment Strategies

### Rolling Update (Default)

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # How many extra pods during update
      maxUnavailable: 0  # How many can be down during update
```

**Process**:
1. Create new pod with new version
2. Wait for pod to be Ready
3. Terminate old pod
4. Repeat until all pods updated

**Pros**: Zero downtime, gradual rollout
**Cons**: Mixed versions running simultaneously

---

### Blue-Green Deployment

```yaml
# Blue (current)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-blue
spec:
  replicas: 3

---
# Green (new)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-green
spec:
  replicas: 3

---
# Service switches between blue and green
apiVersion: v1
kind: Service
metadata:
  name: app
spec:
  selector:
    version: blue  # Change to green when ready
```

**Process**:
1. Deploy new version alongside old
2. Test new version
3. Switch service selector
4. Remove old version

**Pros**: Instant rollback, testing in production
**Cons**: Double resources required

---

### Canary Deployment

```yaml
# Main deployment: 90% traffic
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-stable
spec:
  replicas: 9

---
# Canary deployment: 10% traffic
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-canary
spec:
  replicas: 1
```

**Pros**: Risk mitigation, gradual rollout
**Cons**: Requires advanced traffic splitting

---

## 🔍 Troubleshooting Guide

### Common Issues and Solutions

#### Pod Not Starting

```bash
# Check pod status
kubectl get pods -n roboshop

# Describe pod for events
kubectl describe pod <pod-name> -n roboshop

# Check logs
kubectl logs <pod-name> -n roboshop

# Check previous logs (if crashed)
kubectl logs <pod-name> -n roboshop --previous
```

**Common Causes**:
- Image pull errors (check image name/tag)
- Resource constraints (insufficient CPU/memory)
- ConfigMap/Secret not found
- Invalid volume mounts

---

#### Service Not Accessible

```bash
# Verify service exists
kubectl get svc -n roboshop

# Check endpoints
kubectl get endpoints catalogue -n roboshop

# Test from another pod
kubectl run test --rm -it --image=busybox -n roboshop -- sh
wget -O- http://catalogue:8080/health
```

**Common Causes**:
- Selector mismatch between Service and Pods
- Wrong port configuration
- Pod not in Running state
- No pods matching the selector

---

#### Database Connection Issues

```bash
# Check database pod
kubectl get pods -n roboshop | grep mongodb

# Check database logs
kubectl logs mongodb-<pod-id> -n roboshop

# Verify ConfigMap
kubectl get configmap catalogue -n roboshop -o yaml

# Test DNS resolution
kubectl run test --rm -it --image=busybox -n roboshop -- sh
nslookup mongodb
```

---

#### Application Crashes

```bash
# Check resource usage
kubectl top pods -n roboshop

# Describe pod for OOMKilled events
kubectl describe pod <pod-name> -n roboshop

# Check resource limits
kubectl get pod <pod-name> -n roboshop -o yaml | grep -A 5 resources
```

---

### Debug Commands Reference

```bash
# Get all resources in namespace
kubectl get all -n roboshop

# Watch pod status in real-time
kubectl get pods -n roboshop -w

# Execute command in pod
kubectl exec -it <pod-name> -n roboshop -- sh

# Port forward for local testing
kubectl port-forward svc/web 8080:80 -n roboshop

# Get events
kubectl get events -n roboshop --sort-by='.lastTimestamp'

# Describe all pods
kubectl describe pods -n roboshop

# Get pod YAML
kubectl get pod <pod-name> -n roboshop -o yaml
```

---

## 🏆 Production Best Practices

### 1. High Availability

```yaml
# Multiple replicas
spec:
  replicas: 3

# Pod anti-affinity (spread across nodes)
affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchExpressions:
        - key: app
          operator: In
          values:
          - web
      topologyKey: kubernetes.io/hostname
```

---

### 2. Health Checks

```yaml
containers:
- name: catalogue
  livenessProbe:
    httpGet:
      path: /health
      port: 8080
    initialDelaySeconds: 30
    periodSeconds: 10
  readinessProbe:
    httpGet:
      path: /health
      port: 8080
    initialDelaySeconds: 5
    periodSeconds: 5
```

**Probe Types**:
- **Liveness**: Is the container alive? (restart if fails)
- **Readiness**: Is the container ready for traffic? (remove from service if fails)
- **Startup**: Has the container started? (for slow-starting apps)

---

### 3. Resource Quotas

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: roboshop-quota
  namespace: roboshop
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    pods: "50"
```

---

### 4. Security Best Practices

```yaml
# Run as non-root
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
  
# Read-only root filesystem
containers:
- name: app
  securityContext:
    readOnlyRootFilesystem: true
  volumeMounts:
  - name: tmp
    mountPath: /tmp
volumes:
- name: tmp
  emptyDir: {}
```

---

### 5. Monitoring and Logging

**Logging**:
```yaml
# Application should log to stdout/stderr
# Example in Node.js
const logger = pino({
  level: 'info',
  prettyPrint: false
});
```

**Metrics**:
```javascript
// Prometheus metrics example
const counter = new promClient.Counter({
  name: 'items_added',
  help: 'running count of items added to cart'
});

app.get('/metrics', (req, res) => {
  res.header('Content-Type', 'text/plain');
  res.send(register.metrics());
});
```

---

### 6. Backup and Disaster Recovery

**Database Backups**:
- Use persistent volumes for data
- Implement regular backup jobs
- Test restore procedures
- Store backups in different region/zone

**StatefulSet for Databases** (Advanced):
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mongodb
spec:
  serviceName: mongodb
  replicas: 3
  volumeClaimTemplates:
  - metadata:
      name: mongodb-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 10Gi
```

---

### 7. CI/CD Integration

**GitOps Workflow**:
```
Code Change → Git Push → CI Build → Docker Build → 
Push to Registry → Update Manifest → Apply to Cluster
```

**Deployment Pipeline**:
1. Run tests
2. Build Docker image
3. Tag with version
4. Push to registry
5. Update Kubernetes manifests
6. Apply rolling update
7. Verify health checks
8. Run smoke tests

---

## 📝 Quick Reference

### Deployment Commands

```bash
# Deploy all services
kubectl apply -f 01-namespace.yaml
kubectl apply -f mongodb/manifest.yaml
kubectl apply -f catalogue/manifest.yaml
kubectl apply -f redis/manifest.yaml
kubectl apply -f cart/manifest.yaml
kubectl apply -f mysql/manifest.yaml
kubectl apply -f shipping/manifest.yaml
kubectl apply -f rabbitmq/manifest.yaml
kubectl apply -f payment/manifest.yaml
kubectl apply -f user/manifest.yaml
kubectl apply -f web/manifest.yaml

# Verify deployment
kubectl get all -n roboshop

# Access application
kubectl get svc web -n roboshop
# Access via NodePort: http://<node-ip>:<node-port>
```

---

### Scaling Commands

```bash
# Scale deployment
kubectl scale deployment catalogue --replicas=3 -n roboshop

# Autoscale
kubectl autoscale deployment catalogue --min=2 --max=10 --cpu-percent=80 -n roboshop
```

---

### Update Commands

```bash
# Update image
kubectl set image deployment/catalogue catalogue=sarthak6700/catalogue:v2 -n roboshop

# Rollout status
kubectl rollout status deployment/catalogue -n roboshop

# Rollout history
kubectl rollout history deployment/catalogue -n roboshop

# Rollback
kubectl rollout undo deployment/catalogue -n roboshop
```

---

## 🎓 Key Takeaways

1. **Microservices** enable independent scaling and deployment
2. **Kubernetes** provides orchestration, self-healing, and scaling
3. **ConfigMaps** separate configuration from code
4. **Services** provide stable networking and load balancing
5. **Labels and Selectors** are fundamental to Kubernetes operations
6. **Resource management** prevents resource contention
7. **Health checks** enable self-healing and rolling updates
8. **Multi-stage builds** optimize Docker images
9. **Service discovery** enables loose coupling between services
10. **Observability** is crucial for production systems

---

## 📚 Further Learning

- Kubernetes Official Documentation: https://kubernetes.io/docs
- Docker Best Practices: https://docs.docker.com/develop/dev-best-practices
- 12-Factor App Methodology: https://12factor.net
- Microservices Patterns: https://microservices.io
- CNCF Landscape: https://landscape.cncf.io

---

**Project By**: Sarthak | **Last Updated**: January 2026
