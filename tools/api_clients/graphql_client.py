"""NEXUS AI Agent - GraphQL Client"""

import aiohttp
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class GraphQLResponse:
    """GraphQL response"""
    data: Optional[Dict[str, Any]] = None
    errors: List[Dict[str, Any]] = field(default_factory=list)
    extensions: Dict[str, Any] = field(default_factory=dict)
    success: bool = True


class GraphQLClient:
    """GraphQL API client"""

    def __init__(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30
    ):
        self.endpoint = endpoint
        self.headers = headers or {}
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create session"""
        if self._session is None or self._session.closed:
            default_headers = {
                'Content-Type': 'application/json',
                **self.headers
            }
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers=default_headers
            )
        return self._session

    async def close(self) -> None:
        """Close session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def execute(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None
    ) -> GraphQLResponse:
        """
        Execute GraphQL query

        Args:
            query: GraphQL query string
            variables: Query variables
            operation_name: Operation name

        Returns:
            GraphQLResponse
        """
        session = await self._get_session()

        payload = {
            'query': query,
        }

        if variables:
            payload['variables'] = variables
        if operation_name:
            payload['operationName'] = operation_name

        try:
            async with session.post(self.endpoint, json=payload) as response:
                result = await response.json()

                return GraphQLResponse(
                    data=result.get('data'),
                    errors=result.get('errors', []),
                    extensions=result.get('extensions', {}),
                    success='errors' not in result or not result['errors']
                )

        except Exception as e:
            return GraphQLResponse(
                success=False,
                errors=[{'message': str(e)}]
            )

    async def query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> GraphQLResponse:
        """Execute query operation"""
        return await self.execute(query, variables)

    async def mutate(
        self,
        mutation: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> GraphQLResponse:
        """Execute mutation operation"""
        return await self.execute(mutation, variables)

    async def subscribe(
        self,
        subscription: str,
        variables: Optional[Dict[str, Any]] = None
    ):
        """
        Execute subscription (requires WebSocket support)
        This is a simplified implementation
        """
        # Note: Full subscription support requires WebSocket
        raise NotImplementedError("Subscriptions require WebSocket support")

    def build_query(
        self,
        query_type: str,
        fields: List[str],
        args: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None
    ) -> str:
        """
        Build simple GraphQL query

        Args:
            query_type: Query, Mutation, or Subscription
            fields: Fields to select
            args: Query arguments
            name: Operation name

        Returns:
            GraphQL query string
        """
        # Format arguments
        args_str = ""
        if args:
            arg_parts = []
            for key, value in args.items():
                if isinstance(value, str):
                    arg_parts.append(f'{key}: "{value}"')
                elif isinstance(value, bool):
                    arg_parts.append(f'{key}: {str(value).lower()}')
                else:
                    arg_parts.append(f'{key}: {value}')
            args_str = f"({', '.join(arg_parts)})"

        # Format fields
        fields_str = self._format_fields(fields)

        # Build query
        operation = name or query_type.lower()
        return f"""
            {query_type.lower()} {operation} {{
                {operation}{args_str} {{
                    {fields_str}
                }}
            }}
        """.strip()

    def _format_fields(self, fields: List[Any], indent: int = 0) -> str:
        """Format fields for query"""
        parts = []
        for field in fields:
            if isinstance(field, str):
                parts.append(field)
            elif isinstance(field, dict):
                for key, subfields in field.items():
                    if isinstance(subfields, list):
                        subfields_str = self._format_fields(subfields, indent + 1)
                        parts.append(f"{key} {{\n{subfields_str}\n}}")
                    else:
                        parts.append(f"{key} {{ {subfields} }}")

        return '\n'.join(parts)

    async def introspect(self) -> GraphQLResponse:
        """Get schema introspection"""
        introspection_query = """
            query IntrospectionQuery {
                __schema {
                    types {
                        name
                        kind
                        description
                        fields {
                            name
                            type {
                                name
                                kind
                            }
                        }
                    }
                    queryType { name }
                    mutationType { name }
                    subscriptionType { name }
                }
            }
        """
        return await self.execute(introspection_query)

    async def get_type(self, type_name: str) -> GraphQLResponse:
        """Get type information"""
        query = f"""
            query TypeQuery {{
                __type(name: "{type_name}") {{
                    name
                    kind
                    description
                    fields {{
                        name
                        description
                        type {{
                            name
                            kind
                            ofType {{
                                name
                                kind
                            }}
                        }}
                    }}
                }}
            }}
        """
        return await self.execute(query)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

