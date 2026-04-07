import { Elysia } from "elysia";
import { getHAUrl, getHAToken } from "../ha-client";

/** Proxy a request to the HA REST API and return the parsed JSON. */
async function haFetch(path: string, method = "GET", body?: unknown) {
  const url = `${getHAUrl()}${path}`;
  const headers: Record<string, string> = {
    Authorization: `Bearer ${getHAToken()}`,
    "Content-Type": "application/json",
  };
  console.log(`[OPENCLAW XIAOMI] ${method} ${path}`);
  const res = await fetch(url, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let data: any;
  try {
    data = JSON.parse(text);
  } catch {
    data = { raw: text };
  }
  console.log(`[OPENCLAW XIAOMI] ${method} ${path} -> ${res.status}`, JSON.stringify(data).slice(0, 300));
  if (!res.ok) {
    throw new Error(`HA returned ${res.status}: ${JSON.stringify(data)}`);
  }
  return data;
}

export const xiaomiRoutes = new Elysia()

  /**
   * POST /api/xiaomi/setup
   * Body: { cloud_server: "cn" | "sg" | "us" | "de" | "i2" | "ru" }
   *
   * Starts the HA config flow for xiaomi_home, submits the auth_config step,
   * and returns { flow_id, oauth_url } so the frontend can open the OAuth link.
   */
  .post("/api/xiaomi/setup", async ({ body }) => {
    const { cloud_server = "cn" } = body as any;
    console.log(`[OPENCLAW XIAOMI] === SETUP START === cloud_server=${cloud_server}`);

    try {
      // Step 1: Create the config flow
      console.log("[OPENCLAW XIAOMI] Step 1: Creating config flow...");
      let step = await haFetch("/api/config/config_entries/flow", "POST", {
        handler: "xiaomi_home",
      });
      const flowId = step.flow_id;
      console.log(`[OPENCLAW XIAOMI] Step 1 OK: flow_id=${flowId} step=${step.step_id}`);

      // Step 1b: Handle EULA step if present (auto-accept)
      if (step.step_id === "eula") {
        console.log("[OPENCLAW XIAOMI] Step 1b: Accepting EULA...");
        step = await haFetch(
          `/api/config/config_entries/flow/${flowId}`,
          "POST",
          { eula: true }
        );
        console.log(`[OPENCLAW XIAOMI] Step 1b OK: step=${step.step_id}`);
      }

      if (step.step_id !== "auth_config") {
        return new Response(
          JSON.stringify({
            error: "unexpected_step",
            message: `Expected auth_config after EULA, got ${step.step_id}`,
            flow: step,
          }),
          { status: 400, headers: { "Content-Type": "application/json" } }
        );
      }

      // Step 2: Submit auth_config with the chosen cloud server
      // Note: oauth_redirect_url MUST be "http://homeassistant.local:8123" — the Xiaomi HA integration
      // validates this exact string on the HA side and rejects any other value, including different ports.
      // This means Xiaomi OAuth only works when HA is running on port 8123.
      // If HA was assigned a different port due to a conflict (setup.md Step 3b), Xiaomi OAuth will fail.
      // Users in that situation must free port 8123 and restart HA on it before adding Xiaomi.
      console.log(`[OPENCLAW XIAOMI] Step 2: Submitting auth_config (server=${cloud_server})...`);
      const oauthStep = await haFetch(
        `/api/config/config_entries/flow/${flowId}`,
        "POST",
        {
          cloud_server,
          integration_language: "en",
          oauth_redirect_url: "http://homeassistant.local:8123",
          network_detect_config: false,
        }
      );
      console.log(`[OPENCLAW XIAOMI] Step 2 OK: step=${oauthStep.step_id} type=${oauthStep.type}`);

      // The oauth step returns a progress page with the auth URL in description_placeholders
      const oauthUrl =
        oauthStep.description_placeholders?.link_left ||
        oauthStep.description_placeholders?.link ||
        null;

      console.log(`[OPENCLAW XIAOMI] OAuth URL: ${oauthUrl ? oauthUrl.slice(0, 80) + "..." : "NOT FOUND"}`);

      return {
        flow_id: flowId,
        oauth_url: oauthUrl,
        step: oauthStep.step_id,
        type: oauthStep.type,
        raw: oauthStep,
      };
    } catch (error: any) {
      console.error("[OPENCLAW XIAOMI] SETUP FAILED:", error.message);
      return new Response(
        JSON.stringify({ error: "setup_failed", message: error.message }),
        { status: 502, headers: { "Content-Type": "application/json" } }
      );
    }
  })

  /**
   * GET /api/xiaomi/status/:flow_id
   *
   * Polls the current step of the config flow.
   * Returns the step info, and home list when the flow reaches homes_select.
   */
  .get("/api/xiaomi/status/:flow_id", async ({ params }) => {
    const { flow_id } = params;
    console.log(`[OPENCLAW XIAOMI] STATUS poll flow_id=${flow_id}`);

    try {
      const step = await haFetch(
        `/api/config/config_entries/flow/${flow_id}`,
        "GET"
      );

      const result: any = {
        flow_id,
        step_id: step.step_id,
        type: step.type,
      };

      // If we've reached homes_select, extract the home options
      if (step.step_id === "homes_select" && step.data_schema) {
        const homeField = step.data_schema.find(
          (f: any) => f.name === "home_infos"
        );
        if (homeField?.options) {
          result.homes = homeField.options.map(([id, label]: [string, string]) => ({
            id,
            label,
          }));
        }
        console.log(`[OPENCLAW XIAOMI] STATUS: homes_select ready, ${result.homes?.length ?? 0} homes`);
      } else if (step.type === "abort") {
        result.reason = step.reason;
        console.log(`[OPENCLAW XIAOMI] STATUS: ABORTED reason=${step.reason}`);
      } else if (step.type === "create_entry") {
        result.title = step.title;
        console.log(`[OPENCLAW XIAOMI] STATUS: ENTRY CREATED title=${step.title}`);
      } else {
        console.log(`[OPENCLAW XIAOMI] STATUS: step=${step.step_id} type=${step.type} (still in progress)`);
      }

      result.raw = step;
      return result;
    } catch (error: any) {
      console.error(`[OPENCLAW XIAOMI] STATUS FAILED:`, error.message);
      return new Response(
        JSON.stringify({ error: "status_failed", message: error.message }),
        { status: 502, headers: { "Content-Type": "application/json" } }
      );
    }
  })

  /**
   * POST /api/xiaomi/complete/:flow_id
   * Body: { home_infos: ["home_id_1", ...] }
   *
   * Submits the homes_select step to finish the integration setup.
   */
  .post("/api/xiaomi/complete/:flow_id", async ({ params, body }) => {
    const { flow_id } = params;
    const { home_infos = [] } = body as any;
    console.log(`[OPENCLAW XIAOMI] === COMPLETE === flow_id=${flow_id} homes=${JSON.stringify(home_infos)}`);

    try {
      const result = await haFetch(
        `/api/config/config_entries/flow/${flow_id}`,
        "POST",
        {
          home_infos,
          area_name_rule: "room",
          advanced_options: false,
        }
      );

      console.log(`[OPENCLAW XIAOMI] COMPLETE result: type=${result.type} step=${result.step_id ?? "n/a"}`);

      return {
        flow_id,
        type: result.type,
        step_id: result.step_id,
        title: result.title,
        raw: result,
      };
    } catch (error: any) {
      console.error("[OPENCLAW XIAOMI] COMPLETE FAILED:", error.message);
      return new Response(
        JSON.stringify({ error: "complete_failed", message: error.message }),
        { status: 502, headers: { "Content-Type": "application/json" } }
      );
    }
  })

  /**
   * DELETE /api/xiaomi/cancel/:flow_id
   *
   * Aborts an in-progress config flow.
   */
  .delete("/api/xiaomi/cancel/:flow_id", async ({ params }) => {
    const { flow_id } = params;
    console.log(`[OPENCLAW XIAOMI] === CANCEL === flow_id=${flow_id}`);

    try {
      await haFetch(
        `/api/config/config_entries/flow/${flow_id}`,
        "DELETE"
      );
      console.log(`[OPENCLAW XIAOMI] CANCEL OK`);
      return { success: true };
    } catch (error: any) {
      console.error("[OPENCLAW XIAOMI] CANCEL FAILED:", error.message);
      return new Response(
        JSON.stringify({ error: "cancel_failed", message: error.message }),
        { status: 502, headers: { "Content-Type": "application/json" } }
      );
    }
  });
