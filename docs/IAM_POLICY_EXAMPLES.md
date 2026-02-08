# IAM Policy Examples

## Overview

IAM policies control access to objects in the storage system. Policies are evaluated during search and retrieval to ensure users only see content they're authorized to access.

## Policy Structure

```sql
CREATE TABLE iam_policies (
    id UUID PRIMARY KEY,
    principal VARCHAR(255) NOT NULL,
    resource_pattern VARCHAR(1024) NOT NULL,
    actions TEXT[] NOT NULL,
    effect VARCHAR(10) NOT NULL,  -- ALLOW or DENY
    conditions JSONB DEFAULT '{}'
);
```

## Supported Actions

- `s3:GetObject` - Read object
- `s3:PutObject` - Write object
- `s3:DeleteObject` - Delete object
- `s3:ListBucket` - List bucket contents
- `s3:*` - All actions

## Policy Examples

### 1. Allow User Access to Specific Bucket

```sql
INSERT INTO iam_policies (principal, resource_pattern, actions, effect, description)
VALUES (
    'user123',
    'my-bucket/*',
    ARRAY['s3:GetObject'],
    'ALLOW',
    'User123 can read from my-bucket'
);
```

### 2. Public Read Access

```sql
INSERT INTO iam_policies (principal, resource_pattern, actions, effect, description)
VALUES (
    '*',
    'public-bucket/*',
    ARRAY['s3:GetObject'],
    'ALLOW',
    'Public read access to public-bucket'
);
```

### 3. Department-Specific Access

```sql
-- Engineering department
INSERT INTO iam_policies (principal, resource_pattern, actions, effect, description)
VALUES (
    'engineering',
    'engineering/*',
    ARRAY['s3:GetObject', 's3:PutObject'],
    'ALLOW',
    'Engineering team access'
);

-- Finance department
INSERT INTO iam_policies (principal, resource_pattern, actions, effect, description)
VALUES (
    'finance',
    'finance/*',
    ARRAY['s3:GetObject', 's3:PutObject'],
    'ALLOW',
    'Finance team access'
);
```

### 4. Admin Full Access

```sql
INSERT INTO iam_policies (principal, resource_pattern, actions, effect, description)
VALUES (
    'admin',
    '*',
    ARRAY['s3:*'],
    'ALLOW',
    'Administrator full access'
);
```

### 5. Explicit Deny for Sensitive Data

```sql
-- Deny access to sensitive bucket
INSERT INTO iam_policies (principal, resource_pattern, actions, effect, description)
VALUES (
    'contractor-users',
    'sensitive/*',
    ARRAY['s3:*'],
    'DENY',
    'Contractors cannot access sensitive data'
);
```

**Note**: DENY policies always take precedence over ALLOW policies.

### 6. Project-Based Access

```sql
-- Allow access to project alpha files
INSERT INTO iam_policies (principal, resource_pattern, actions, effect, description)
VALUES (
    'project-alpha-team',
    'projects/alpha/*',
    ARRAY['s3:GetObject', 's3:PutObject'],
    'ALLOW',
    'Project Alpha team access'
);

-- Allow access to project beta files
INSERT INTO iam_policies (principal, resource_pattern, actions, effect, description)
VALUES (
    'project-beta-team',
    'projects/beta/*',
    ARRAY['s3:GetObject', 's3:PutObject'],
    'ALLOW',
    'Project Beta team access'
);
```

### 7. Read-Only Access

```sql
INSERT INTO iam_policies (principal, resource_pattern, actions, effect, description)
VALUES (
    'auditors',
    '*',
    ARRAY['s3:GetObject', 's3:ListBucket'],
    'ALLOW',
    'Auditors have read-only access to all data'
);
```

### 8. Prefix-Based Access Control

```sql
-- Users can access their own prefix
INSERT INTO iam_policies (principal, resource_pattern, actions, effect, description)
VALUES (
    'user-alice',
    'users/alice/*',
    ARRAY['s3:*'],
    'ALLOW',
    'Alice has full access to her files'
);

INSERT INTO iam_policies (principal, resource_pattern, actions, effect, description)
VALUES (
    'user-bob',
    'users/bob/*',
    ARRAY['s3:*'],
    'ALLOW',
    'Bob has full access to his files'
);
```

### 9. Conditional Access (Using JSONB Conditions)

```sql
-- Access only during business hours (example structure)
INSERT INTO iam_policies (principal, resource_pattern, actions, effect, conditions, description)
VALUES (
    'contractors',
    'shared/*',
    ARRAY['s3:GetObject'],
    'ALLOW',
    '{"time": {"start": "09:00", "end": "17:00"}}'::jsonb,
    'Contractors can access shared files during business hours'
);
```

**Note**: Condition evaluation would need to be implemented in the IAMAuthorizer class.

### 10. Group-Based Access

```sql
-- Marketing group
INSERT INTO iam_policies (principal, resource_pattern, actions, effect, description)
VALUES (
    'group:marketing',
    'marketing/*',
    ARRAY['s3:GetObject', 's3:PutObject'],
    'ALLOW',
    'Marketing group access'
);

-- Sales group
INSERT INTO iam_policies (principal, resource_pattern, actions, effect, description)
VALUES (
    'group:sales',
    'sales/*',
    ARRAY['s3:GetObject', 's3:PutObject'],
    'ALLOW',
    'Sales group access'
);
```

## Wildcard Patterns

- `*` matches any characters
- `bucket/*` matches all objects in bucket
- `bucket/prefix/*` matches all objects under prefix
- `bucket/file.txt` matches exact object

## Best Practices

1. **Principle of Least Privilege**: Grant minimum necessary permissions
2. **Use Explicit DENY**: For sensitive data, use DENY policies
3. **Group Policies**: Use group-based policies for team access
4. **Audit Regularly**: Review and update policies periodically
5. **Test Policies**: Test with different principals before deploying
6. **Document Policies**: Add clear descriptions to all policies

## Testing Policies

```python
from iam_authorizer import IAMAuthorizer
from metadata_store import MetadataStore

# Initialize
store = MetadataStore(connection_string)
authorizer = IAMAuthorizer(store)

# Test authorization
result = authorizer.authorize(
    principal="user123",
    resource="my-bucket/file.txt",
    action="s3:GetObject"
)

print(f"Access {'granted' if result else 'denied'}")
```

## Policy Evaluation Order

1. Explicit DENY policies are evaluated first
2. If any DENY matches, access is denied immediately
3. Then ALLOW policies are evaluated
4. If any ALLOW matches, access is granted
5. If no policies match, access is denied (default deny)

## Managing Policies

### Add Policy
```sql
INSERT INTO iam_policies (principal, resource_pattern, actions, effect, description)
VALUES ('user', 'bucket/*', ARRAY['s3:GetObject'], 'ALLOW', 'Description');
```

### Update Policy
```sql
UPDATE iam_policies
SET actions = ARRAY['s3:GetObject', 's3:PutObject']
WHERE principal = 'user' AND resource_pattern = 'bucket/*';
```

### Delete Policy
```sql
DELETE FROM iam_policies
WHERE principal = 'user' AND resource_pattern = 'bucket/*';
```

### List Policies for Principal
```sql
SELECT * FROM iam_policies
WHERE principal = 'user' OR principal = '*'
ORDER BY effect DESC;  -- DENY first
```
