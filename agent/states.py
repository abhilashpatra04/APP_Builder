from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class File(BaseModel):
    path: str = Field(description="The path to the file to be created or modified")
    purpose: str = Field(
        description="The purpose of the file, e.g. 'main application logic', 'data processing module', etc.")


class Plan(BaseModel):
    name: str = Field(description="The name of app to be built")
    description: str = Field(
        description="A oneline description of the app to be built, e.g. 'A web application for managing personal finances'")
    techs_tack: str = Field(
        description="The tech stack to be used for the app, e.g. 'python', 'javascript', 'react', 'flask', etc.")
    features: list[str] = Field(
        description="A list of features that the app should have, e.g. 'user authentication', 'data visualization', etc.")
    files: list[File] = Field(description="A list of files to be created, each with a 'path' and 'purpose'")


class ImplementationTask(BaseModel):
    filepath: str = Field(description="The path to the file to be modified")
    task_description: str = Field(
        description="A detailed description of the task to be performed on the file, e.g. 'add user authentication', 'implement data processing logic', etc.")


class TaskPlan(BaseModel):
    implementation_steps: list[ImplementationTask] = Field(
        description="A list of steps to be taken to implement the task")
    model_config = ConfigDict(extra="allow")


class CoderState(BaseModel):
    task_plan: TaskPlan = Field(description="The plan for the task to be implemented")
    current_step_idx: int = Field(0, description="The index of the current step in the implementation steps")
    current_file_content: Optional[str] = Field(None,
                                                description="The content of the file currently being edited or created")
    retry_count: int = Field(0, description="Number of retries for current step")


class EnhancedPlan(BaseModel):
    name: str = Field(description="The name of app to be built")
    description: str = Field(description="A one-line description of the app")
    features: list[str] = Field(description="List of features the app should have")
    files: list[File] = Field(description="List of files to be created")
    
    required_tech_stacks: list[str] = Field(default_factory=list, description="Detected tech stacks: react, python, etc.")
    frontend_tech: Optional[str] = Field(None, description="Frontend: react, vue, vanilla, or None")
    backend_tech: Optional[str] = Field(None, description="Backend: python, nodejs, or None")
    database_tech: Optional[str] = Field(None, description="Database: postgresql, mongodb, sqlite, or None")
    deployment_tech: Optional[str] = Field(None, description="Deployment: docker or None")
    tech_stack_reasoning: str = Field("", description="Why these stacks were chosen")
    
    review_status: str = Field("pending", description="pending, approved, rejected")
    user_edits: Optional[str] = Field(None, description="User modification requests")


class ReviewResult(BaseModel):
    stage: str = Field(description="plan_review or task_review")
    status: str = Field(description="approved, edit, regenerate")
    errors: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class GlobalContext(BaseModel):
    interfaces: dict[str, str] = Field(default_factory=dict, description="file -> interface definition")
    contracts: list[str] = Field(default_factory=list, description="Shared contracts")
    shared_types: dict[str, str] = Field(default_factory=dict, description="Common type definitions")
    project_files: list[str] = Field(default_factory=list, description="All project file paths")


class FileDiff(BaseModel):
    filepath: str
    before_content: Optional[str] = None
    after_content: str
    status: str = Field("created", description="created, modified, deleted")