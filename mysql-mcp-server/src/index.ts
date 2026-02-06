#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import mysql from "mysql2/promise";

// 手动加载 .env,完全静默
import { readFileSync } from 'fs';
import { resolve } from 'path';

try {
  const envPath = resolve(process.cwd(), '.env');
  const envContent = readFileSync(envPath, 'utf-8');
  envContent.split('\n').forEach(line => {
    const match = line.match(/^([^=:#]+)=(.*)$/);
    if (match) {
      const key = match[1].trim();
      const value = match[2].trim();
      if (!process.env[key]) {
        process.env[key] = value;
      }
    }
  });
} catch (error) {
  // .env 文件不存在也没关系,从环境变量读取
}

let pool: mysql.Pool;

async function initDatabase() {
  pool = mysql.createPool({
    host: process.env.MYSQL_HOST,
    port: parseInt(process.env.MYSQL_PORT || "3306"),
    user: process.env.MYSQL_USER,
    password: process.env.MYSQL_PASSWORD,
    database: process.env.MYSQL_DATABASE,
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0,
    enableKeepAlive: true,
    keepAliveInitialDelay: 0,
  });

  try {
    const connection = await pool.getConnection();
    connection.release();
  } catch (error) {
    throw error;
  }
}

const server = new Server(
  {
    name: "mysql-mcp-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
      resources: {},
    },
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "query",
        description: "Execute a SELECT query on the MySQL database. Returns results as JSON.",
        inputSchema: {
          type: "object",
          properties: {
            sql: {
              type: "string",
              description: "The SQL SELECT query to execute",
            },
          },
          required: ["sql"],
        },
      },
      {
        name: "list_tables",
        description: "List all tables in the current database",
        inputSchema: {
          type: "object",
          properties: {},
        },
      },
      {
        name: "describe_table",
        description: "Get the structure of a specific table",
        inputSchema: {
          type: "object",
          properties: {
            table: {
              type: "string",
              description: "The name of the table to describe",
            },
          },
          required: ["table"],
        },
      },
      {
        name: "execute",
        description: "Execute INSERT, UPDATE, or DELETE query (only if READ_ONLY is false)",
        inputSchema: {
          type: "object",
          properties: {
            sql: {
              type: "string",
              description: "The SQL query to execute",
            },
          },
          required: ["sql"],
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "query": {
        const { sql } = args as { sql: string };

        const trimmedSql = sql.trim().toUpperCase();
        if (!trimmedSql.startsWith("SELECT") && !trimmedSql.startsWith("SHOW") && !trimmedSql.startsWith("DESCRIBE")) {
          throw new Error("Only SELECT, SHOW, and DESCRIBE queries are allowed");
        }

        const maxRows = parseInt(process.env.MAX_ROWS || "1000");
        const limitedSql = sql.includes("LIMIT") ? sql : `${sql} LIMIT ${maxRows}`;

        const [rows] = await pool.query(limitedSql);

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(rows, null, 2),
            },
          ],
        };
      }

      case "list_tables": {
        const [tables] = await pool.query("SHOW TABLES");
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(tables, null, 2),
            },
          ],
        };
      }

      case "describe_table": {
        const { table } = args as { table: string };
        const safeName = table.replace(/[^a-zA-Z0-9_]/g, '');
        const [columns] = await pool.query(`DESCRIBE \`${safeName}\``);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(columns, null, 2),
            },
          ],
        };
      }

      case "execute": {
        if (process.env.READ_ONLY === "true") {
          throw new Error("Write operations are disabled in READ_ONLY mode");
        }

        const { sql } = args as { sql: string };
        const [result] = await pool.query(sql);

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    return {
      content: [
        {
          type: "text",
          text: `Error: ${errorMessage}`,
        },
      ],
      isError: true,
    };
  }
});

server.setRequestHandler(ListResourcesRequestSchema, async () => {
  try {
    const [tables] = await pool.query("SHOW TABLES");
    const tableNames = (tables as any[]).map(row => Object.values(row)[0] as string);

    return {
      resources: tableNames.map(table => ({
        uri: `schema://${table}`,
        name: `Schema: ${table}`,
        mimeType: "application/json",
        description: `Table structure for ${table}`,
      })),
    };
  } catch (error) {
    return { resources: [] };
  }
});

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const uri = request.params.uri;
  const match = uri.match(/^schema:\/\/(.+)$/);

  if (!match) {
    throw new Error(`Invalid resource URI: ${uri}`);
  }

  const tableName = match[1];
  const safeName = tableName.replace(/[^a-zA-Z0-9_]/g, '');
  const [columns] = await pool.query(`DESCRIBE \`${safeName}\``);

  return {
    contents: [
      {
        uri,
        mimeType: "application/json",
        text: JSON.stringify(columns, null, 2),
      },
    ],
  };
});

async function main() {
  await initDatabase();
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main();