import { authFetch } from './authFetch';

export interface ActionRecord {
   id: string;
   opportunity_id?: string | null;
   user_id?: string | null;
   action_type?: string | null;
   schedule_type?: string | null;
   schedule_config?: Record<string, unknown> | null;
   config?: Record<string, unknown> | null;
   status?: string | null;
   next_execution_at?: string | null;
   last_executed_at?: string | null;
   created_at?: string | null;
   updated_at?: string | null;
}

export interface ActionLogRecord {
   id: string;
   action_id?: string | null;
   type?: string | null;
   status?: string | null;
   message?: string | null;
   created_at?: string | null;
}

export interface ActionUpsertPayload {
   opportunity_id?: string;
   action_type: string;
   schedule_type: string;
   schedule_config?: Record<string, unknown>;
   config?: Record<string, unknown>;
   max_executions?: number | null;
}

function authHeaders(): HeadersInit {
   return {
      'Content-Type': 'application/json',
   };
}

async function readPayload(res: Response): Promise<any> {
   return await res.json().catch(() => ({}));
}

export async function listOpportunityActions(
   opportunityId: string,
   token: string
): Promise<ActionRecord[]> {
   const res = await authFetch(
      `/api/opportunities/${encodeURIComponent(opportunityId)}/actions`,
      {},
      token
   );
   const payload = await readPayload(res);
   if (!res.ok) {
      throw new Error(
         payload?.message || payload?.error || 'Erreur lors du chargement des actions'
      );
   }
   return payload?.actions || [];
}

export async function createAction(
   data: ActionUpsertPayload,
   token: string
): Promise<ActionRecord> {
   const res = await authFetch(
      '/api/actions',
      {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(data),
      },
      token
   );
   const payload = await readPayload(res);
   if (!res.ok) {
      throw new Error(
         payload?.message || payload?.error || 'Erreur lors de la création de l’action'
      );
   }
   return payload.action;
}

export async function updateAction(
   actionId: string,
   data: ActionUpsertPayload,
   token: string
): Promise<ActionRecord> {
   const res = await authFetch(
      `/api/actions/${actionId}`,
      {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify(data),
      },
      token
   );
   const payload = await readPayload(res);
   if (!res.ok) {
      throw new Error(
         payload?.message || payload?.error || 'Erreur lors de la mise à jour de l’action'
      );
   }
   return payload.action;
}

export async function deleteAction(actionId: string, token: string): Promise<void> {
   const res = await authFetch(
      `/api/actions/${actionId}`,
      {
      method: 'DELETE',
      },
      token
   );
   const payload = await readPayload(res);
   if (!res.ok) {
      throw new Error(
         payload?.message || payload?.error || 'Erreur lors de la suppression de l’action'
      );
   }
}

export async function pauseAction(actionId: string, token: string): Promise<ActionRecord> {
   const res = await authFetch(
      `/api/actions/${actionId}/pause`,
      {
      method: 'POST',
      },
      token
   );
   const payload = await readPayload(res);
   if (!res.ok) {
      throw new Error(payload?.message || payload?.error || 'Erreur lors de la pause de l’action');
   }
   return payload.action;
}

export async function resumeAction(actionId: string, token: string): Promise<ActionRecord> {
   const res = await authFetch(
      `/api/actions/${actionId}/resume`,
      {
      method: 'POST',
      },
      token
   );
   const payload = await readPayload(res);
   if (!res.ok) {
      throw new Error(
         payload?.message || payload?.error || 'Erreur lors de la reprise de l’action'
      );
   }
   return payload.action;
}

export async function executeAction(
   actionId: string,
   token: string
): Promise<Record<string, unknown>> {
   const res = await authFetch(
      `/api/action/${actionId}/execute`,
      {
      method: 'POST',
      },
      token
   );
   const payload = await readPayload(res);
   if (!res.ok) {
      throw new Error(
         payload?.message || payload?.error || 'Erreur lors de l’exécution de l’action'
      );
   }
   return payload;
}

export async function getActionLogs(
   actionId: string,
   token: string,
   limit: number = 50
): Promise<ActionLogRecord[]> {
   const res = await authFetch(`/api/actions/${actionId}/logs?limit=${limit}`, {}, token);
   const payload = await readPayload(res);
   if (!res.ok) {
      throw new Error(
         payload?.message || payload?.error || 'Erreur lors du chargement des logs d’action'
      );
   }
   return payload?.logs || [];
}
