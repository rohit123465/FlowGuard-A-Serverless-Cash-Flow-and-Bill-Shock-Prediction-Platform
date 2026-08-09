import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { notificationApi } from "../../api/endpoints";
import { useAuth } from "../../hooks/useAuth";

const pounds = (minor: number) => new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP" }).format(minor / 100);

export function NotificationInbox() {
  const { getAccessToken } = useAuth();
  const api = useMemo(() => notificationApi(getAccessToken), [getAccessToken]);
  const queryClient = useQueryClient();
  const notifications = useQuery({ queryKey: ["notifications"], queryFn: api.list, refetchInterval: 60_000 });
  const markRead = useMutation({ mutationFn: api.markRead, onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }) });
  const unread = notifications.data?.filter((item) => !item.read) ?? [];
  if (!unread.length) return null;
  return <section className="notification-inbox" aria-live="polite">{unread.map((item) => <article key={item.notification_id}><div><strong>Bill-shock warning</strong><p>Your balance is forecast to fall {pounds(item.shortfall_amount_minor)} below your {pounds(item.safety_buffer_minor)} safety buffer on {new Date(`${item.first_shortfall_date}T00:00:00`).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" })}.</p>{item.risk_probability != null && <p><strong>Estimated shortfall risk: {Math.round(item.risk_probability * 100)}%</strong> using the experimental logistic-regression model.</p>}</div><button onClick={() => markRead.mutate(item.notification_id)} disabled={markRead.isPending}>Dismiss</button></article>)}</section>;
}
