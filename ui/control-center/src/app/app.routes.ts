import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    title: 'Overview · ITRU Control Center',
    loadComponent: () => import('./features/overview/overview').then((m) => m.Overview),
  },
  {
    path: 'runs',
    title: 'Runs · ITRU Control Center',
    loadComponent: () => import('./features/runs/runs').then((m) => m.Runs),
  },
  {
    path: 'runs/:runId',
    title: 'Run detail · ITRU Control Center',
    loadComponent: () => import('./features/runs/run-detail').then((m) => m.RunDetailPage),
  },
  {
    path: 'tasks',
    title: 'Tasks · ITRU Control Center',
    loadComponent: () => import('./features/tasks/tasks').then((m) => m.Tasks),
  },
  {
    path: 'tasks/:taskId',
    title: 'Task detail · ITRU Control Center',
    loadComponent: () => import('./features/tasks/task-detail').then((m) => m.TaskDetailPage),
  },
  {
    path: 'agents',
    title: 'Agents · ITRU Control Center',
    loadComponent: () => import('./features/agents/agents').then((m) => m.Agents),
  },
  {
    path: 'approvals',
    title: 'Approvals · ITRU Control Center',
    loadComponent: () => import('./features/approvals/approvals').then((m) => m.Approvals),
  },
  {
    path: '**',
    title: 'Not found · ITRU Control Center',
    loadComponent: () => import('./features/not-found/not-found').then((m) => m.NotFound),
  },
];
