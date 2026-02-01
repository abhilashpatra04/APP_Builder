CURATED_REPOS = {
    "react": {
        "ui_libraries": [
            {
                "url": "https://github.com/shadcn-ui/ui",
                "stars": 70000,
                "reason": "Modern component library with excellent patterns",
                "extract_paths": ["**/*.tsx"],
                "priority": "high"
            },
            {
                "url": "https://github.com/mantinedev/mantine",
                "stars": 25000,
                "reason": "Production-ready components with hooks",
                "extract_paths": ["**/*.tsx"],
                "priority": "high"
            },
            {
                "url": "https://github.com/radix-ui/primitives",
                "stars": 15000,
                "reason": "Unstyled accessible components",
                "extract_paths": ["**/*.tsx"],
                "priority": "medium"
            }
        ],
        "authentication": [
            {
                "url": "https://github.com/nextauthjs/next-auth",
                "stars": 20000,
                "reason": "Industry standard auth for Next.js",
                "extract_paths": ["packages/core/src/**/*.ts", "packages/next-auth/src/**/*.ts"],
                "priority": "high"
            },
            {
                "url": "https://github.com/clerk/javascript",
                "stars": 3000,
                "reason": "Modern auth SDK patterns",
                "extract_paths": ["packages/react/src/**/*.tsx"],
                "priority": "medium"
            }
        ],
        "full_apps": [
            {
                "url": "https://github.com/alan2207/bulletproof-react",
                "stars": 25000,
                "reason": "React architecture best practices",
                "extract_paths": ["src/**/*.tsx", "src/**/*.ts"],
                "priority": "high"
            },
            {
                "url": "https://github.com/vercel/commerce",
                "stars": 10000,
                "reason": "Real-world e-commerce by Vercel",
                "extract_paths": ["site/**/*.tsx"],
                "priority": "medium"
            },
            {
                "url": "https://github.com/calcom/cal.com",
                "stars": 30000,
                "reason": "Production scheduling app",
                "extract_paths": ["apps/web/components/**/*.tsx"],
                "priority": "medium"
            }
        ],
        "forms": [
            {
                "url": "https://github.com/react-hook-form/react-hook-form",
                "stars": 40000,
                "reason": "Most popular form library",
                "extract_paths": ["src/**/*.ts"],
                "priority": "high"
            }
        ],
        "state_management": [
            {
                "url": "https://github.com/pmndrs/zustand",
                "stars": 45000,
                "reason": "Simple state management",
                "extract_paths": ["src/**/*.ts"],
                "priority": "high"
            },
            {
                "url": "https://github.com/TanStack/query",
                "stars": 40000,
                "reason": "Server state management",
                "extract_paths": ["packages/react-query/src/**/*.ts"],
                "priority": "high"
            }
        ]
    },
    "python": {
        "fastapi": [
            {
                "url": "https://github.com/tiangolo/full-stack-fastapi-template",
                "stars": 25000,
                "reason": "Official FastAPI production template",
                "extract_paths": ["backend/app/**/*.py"],
                "priority": "high"
            },
            {
                "url": "https://github.com/nsidnev/fastapi-realworld-example-app",
                "stars": 3000,
                "reason": "Real-world FastAPI patterns",
                "extract_paths": ["app/**/*.py"],
                "priority": "high"
            },
            {
                "url": "https://github.com/zhanymkanov/fastapi-best-practices",
                "stars": 7000,
                "reason": "FastAPI best practices guide",
                "extract_paths": ["**/*.py"],
                "priority": "high"
            }
        ],
        "authentication": [
            {
                "url": "https://github.com/fastapi-users/fastapi-users",
                "stars": 4000,
                "reason": "Complete auth system for FastAPI",
                "extract_paths": ["fastapi_users/**/*.py"],
                "priority": "high"
            }
        ],
        "database": [
            {
                "url": "https://github.com/tiangolo/sqlmodel",
                "stars": 13000,
                "reason": "SQL databases with Pydantic",
                "extract_paths": ["sqlmodel/**/*.py"],
                "priority": "high"
            },
            {
                "url": "https://github.com/encode/databases",
                "stars": 3600,
                "reason": "Async database support",
                "extract_paths": ["databases/**/*.py"],
                "priority": "medium"
            }
        ],
        "utilities": [
            {
                "url": "https://github.com/pydantic/pydantic",
                "stars": 20000,
                "reason": "Data validation patterns",
                "extract_paths": ["pydantic/**/*.py"],
                "priority": "high"
            }
        ]
    },
    "vue": {
        "component_libraries": [
            {
                "url": "https://github.com/element-plus/element-plus",
                "stars": 23000,
                "reason": "Enterprise-grade Vue components",
                "extract_paths": ["packages/components/**/*.vue", "packages/components/**/*.ts"],
                "priority": "high"
            },
            {
                "url": "https://github.com/vuetifyjs/vuetify",
                "stars": 39000,
                "reason": "Material Design components",
                "extract_paths": ["packages/vuetify/src/components/**/*.tsx"],
                "priority": "high"
            }
        ],
        "full_apps": [
            {
                "url": "https://github.com/vbenjs/vue-vben-admin",
                "stars": 23000,
                "reason": "Production admin template",
                "extract_paths": ["src/**/*.vue", "src/**/*.ts"],
                "priority": "high"
            }
        ],
        "composables": [
            {
                "url": "https://github.com/vueuse/vueuse",
                "stars": 19000,
                "reason": "Essential Vue composables",
                "extract_paths": ["packages/core/**/*.ts"],
                "priority": "high"
            }
        ]
    },
    "nodejs": {
        "express_apis": [
            {
                "url": "https://github.com/hagopj13/node-express-boilerplate",
                "stars": 7000,
                "reason": "Production Express API structure",
                "extract_paths": ["src/**/*.js"],
                "priority": "high"
            },
            {
                "url": "https://github.com/santiq/bulletproof-nodejs",
                "stars": 5000,
                "reason": "Node.js architecture best practices",
                "extract_paths": ["src/**/*.ts"],
                "priority": "high"
            }
        ],
        "authentication": [
            {
                "url": "https://github.com/jaredhanson/passport",
                "stars": 22000,
                "reason": "Authentication middleware",
                "extract_paths": ["lib/**/*.js"],
                "priority": "high"
            }
        ],
        "nestjs": [
            {
                "url": "https://github.com/nestjs/nest",
                "stars": 65000,
                "reason": "Enterprise Node.js framework",
                "extract_paths": ["packages/core/src/**/*.ts"],
                "priority": "high"
            }
        ]
    },
    "docker": {
        "best_practices": [
            {
                "url": "https://github.com/docker/awesome-compose",
                "stars": 30000,
                "reason": "Official Docker compose examples",
                "extract_paths": ["*/compose.yaml", "*/Dockerfile", "*/docker-compose.yml"],
                "priority": "high"
            }
        ],
        "production": [
            {
                "url": "https://github.com/goldbergyoni/nodebestpractices",
                "stars": 97000,
                "reason": "Node.js Docker patterns",
                "extract_paths": ["**/Dockerfile", "**/*.dockerfile"],
                "priority": "medium"
            }
        ]
    }
}


def get_repos_for_tech(tech_stack: str) -> list:
    if tech_stack not in CURATED_REPOS:
        return []
    
    repos = []
    for category, repo_list in CURATED_REPOS[tech_stack].items():
        for repo in repo_list:
            repos.append({**repo, "category": category})
    return repos


def get_high_priority_repos(tech_stack: str) -> list:
    return [r for r in get_repos_for_tech(tech_stack) if r.get("priority") == "high"]
