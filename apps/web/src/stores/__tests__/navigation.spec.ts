import { describe, expect, it } from "vitest";

import { filterNavItems } from "@/config/navigation";

describe("filterNavItems", () => {
  it("keeps admin and delivery pages out of provider navigation", () => {
    const names = filterNavItems("provider").map((item) => item.name);

    expect(names).not.toContain("admin-approvals");
    expect(names).not.toContain("admin-users");
    expect(names).not.toContain("admin-audit-logs");
    expect(names).not.toContain("admin-processors");
    expect(names).not.toContain("deliveries");
  });

  it("keeps business flows out of admin navigation", () => {
    const names = filterNavItems("admin").map((item) => item.name);

    expect(names).toContain("admin-approvals");
    expect(names).toContain("admin-users");
    expect(names).toContain("admin-audit-logs");
    expect(names).toContain("admin-processors");
    expect(names).not.toContain("deliveries");
  });
});
