Project Name

SkyFi MCP Server

Project Description

A local-first Model Context Protocol (MCP) server that wraps the SkyFi public API and related tools (e.g., weather, OpenStreetMap) into agent-friendly, schema-validated endpoints compatible with LangGraph, Claude, OpenAI, and other LLM tool interfaces.

Target Audience

Developers and AI researchers building autonomous agents that consume geospatial data from SkyFi for reasoning, querying, and planning tasks.

Desired Features

MCP Server Features
	•	Expose all SkyFi public API endpoints as tool calls
	•	JSON Schema definitions for each tool (input/output)
	•	Local-first API key support via config.json
	•	SSE-compatible HTTP responses for streaming tools
	•	GET /mcp/manifest returning tool list and schemas
	•	Weather API tool wrapper
	•	OpenStreetMap tool wrapper
	•	Stateless HTTP endpoints
	•	Optional support for Authorization: Bearer headers

Developer Support
	•	Clear README and setup instructions
	•	Documentation for Claude, LangGraph, ai-sdk, Gemini
	•	Code samples for tool calling
	•	Example config for local testing
	•	Curl/Postman testing scripts

Demo Agent
	•	LangGraph / Claude / Gemini agent that:
	•	Uses SkyFi tool to search for satellite images
	•	Uses Weather tool to assess feasibility
	•	Calculates cost or makes a recommendation
	•	Local Python demo (demo_agent.py) or Claude demo

Design Requests
	•	Clear modular file layout (tools/, schemas/, server.py)
	•	Developer-oriented logs (requests/responses)
	•	JSON schema auto-validation per tool

Timeline & Milestones

Milestone	Deadline
Base MCP Server w/ SkyFi Tools	Tue PM
MVP Server + Weather + Docs	Fri PM
Stretch Goals (Agent, Video, OSS PR)	Sun PM

Stretch Goals
	•	Integration into NalaMap OSS
	•	Walkthrough videos (Claude + Cursor)
	•	Blog post with architecture/code samples
	•	Agent with sampling + guardrails
	•	Gemini and OpenAI walkthroughs

Open Questions
	•	Should we also wrap image ordering endpoints?
	•	What minimum number of tools = MVP?
	•	Do we want to auto-generate schemas or hand-write them?