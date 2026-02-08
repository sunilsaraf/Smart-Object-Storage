"""
IAM authorization for access control.
Evaluates IAM policies against resources and actions.
"""
import logging
import re
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class IAMAuthorizer:
    """IAM policy authorizer for access control."""
    
    def __init__(self, metadata_store):
        """
        Initialize IAM authorizer.
        
        Args:
            metadata_store: Metadata store for policy retrieval
        """
        self.metadata_store = metadata_store
        
    def authorize(self, principal: str, resource: str, action: str) -> bool:
        """
        Check if principal is authorized for action on resource.
        
        Args:
            principal: Principal identifier (user, role, etc.)
            resource: Resource path (e.g., "bucket-name/object-key")
            action: Action (e.g., "s3:GetObject")
            
        Returns:
            True if authorized, False otherwise
        """
        # Get applicable policies
        policies = self.metadata_store.get_iam_policies(principal)
        
        # Evaluate policies
        # DENY takes precedence over ALLOW
        has_allow = False
        has_deny = False
        
        for policy in policies:
            if self._matches_resource(policy["resource_pattern"], resource):
                if action in policy["actions"] or "*" in policy["actions"]:
                    if policy["effect"] == "DENY":
                        has_deny = True
                        break
                    elif policy["effect"] == "ALLOW":
                        has_allow = True
                        
        # If any DENY, return False
        if has_deny:
            logger.info(f"Access denied for {principal} on {resource} (explicit DENY)")
            return False
            
        # If any ALLOW, return True
        if has_allow:
            logger.debug(f"Access granted for {principal} on {resource}")
            return True
            
        # Default deny
        logger.info(f"Access denied for {principal} on {resource} (no matching ALLOW)")
        return False
        
    def _matches_resource(self, pattern: str, resource: str) -> bool:
        """
        Check if resource matches pattern.
        
        Args:
            pattern: Resource pattern (supports * wildcard)
            resource: Actual resource path
            
        Returns:
            True if matches, False otherwise
        """
        # Convert wildcard pattern to regex
        # * matches any characters
        regex_pattern = pattern.replace("*", ".*")
        regex_pattern = f"^{regex_pattern}$"
        
        return bool(re.match(regex_pattern, resource))
        
    def filter_results(self, principal: str, results: List[Dict], 
                      action: str = "s3:GetObject") -> List[Dict]:
        """
        Filter search results based on IAM policies.
        
        Args:
            principal: Principal identifier
            results: List of search results
            action: Action to check authorization for
            
        Returns:
            Filtered list of authorized results
        """
        authorized_results = []
        
        for result in results:
            bucket = result.get("bucket", "")
            key = result.get("key", "")
            resource = f"{bucket}/{key}"
            
            if self.authorize(principal, resource, action):
                authorized_results.append(result)
            else:
                logger.debug(f"Filtered out unauthorized result: {resource}")
                
        logger.info(f"Filtered {len(results)} results to {len(authorized_results)} authorized results")
        return authorized_results
        
    def batch_authorize(self, principal: str, resources: List[str], 
                       action: str) -> Dict[str, bool]:
        """
        Batch authorization check for multiple resources.
        
        Args:
            principal: Principal identifier
            resources: List of resource paths
            action: Action to check
            
        Returns:
            Dictionary mapping resource to authorization result
        """
        results = {}
        for resource in resources:
            results[resource] = self.authorize(principal, resource, action)
        return results
