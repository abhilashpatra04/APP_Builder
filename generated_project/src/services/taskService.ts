import axios, { AxiosError } from 'axios';
import { Task } from '../models/Task';

class TaskService {
  private apiUrl: string;

  constructor(apiUrl: string) {
    this.apiUrl = apiUrl;
  }

  async fetchTasks(): Promise<Task[]> {
    try {
      const response = await axios.get(`${this.apiUrl}/tasks`);
      return response.data as Task[];
    } catch (error) {
      if (error instanceof AxiosError) {
        throw new Error(`Failed to fetch tasks: ${error.message}`);
      } else {
        throw error;
      }
    }
  }

  async createTask(task: Task): Promise<Task> {
    try {
      const response = await axios.post(`${this.apiUrl}/tasks`, task);
      return response.data as Task;
    } catch (error) {
      if (error instanceof AxiosError) {
        throw new Error(`Failed to create task: ${error.message}`);
      } else {
        throw error;
      }
    }
  }

  async deleteTask(id: string): Promise<void> {
    try {
      await axios.delete(`${this.apiUrl}/tasks/${id}`);
    } catch (error) {
      if (error instanceof AxiosError) {
        throw new Error(`Failed to delete task: ${error.message}`);
      } else {
        throw error;
      }
    }
  }

  async editTask(id: string, task: Task): Promise<Task> {
    try {
      const response = await axios.put(`${this.apiUrl}/tasks/${id}`, task);
      return response.data as Task;
    } catch (error) {
      if (error instanceof AxiosError) {
        throw new Error(`Failed to edit task: ${error.message}`);
      } else {
        throw error;
      }
    }
  }
}

export default TaskService;
