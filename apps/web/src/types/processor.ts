export interface Processor {
  id: number;
  name: string;
  taskType: string;
  description: string;
  endpointUrl: string;
  status: "online" | "offline";
  lastHeartbeatAt: string;
  registeredAt: string;
}
