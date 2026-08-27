import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Sidebar } from "./Sidebar";
import type { Conversation } from "@/lib/chat";

const conversations: Conversation[] = [
  { id: "1", title: "What is Berlin?" },
  { id: "2", title: "What is Tokyo?" },
];

describe("Sidebar", () => {
  it("renders every conversation's title", () => {
    render(
      <Sidebar
        open={true}
        conversations={conversations}
        activeConversationId="1"
        onNewChat={vi.fn()}
        onSelectConversation={vi.fn()}
      />,
    );

    expect(screen.getByText("What is Berlin?")).toBeInTheDocument();
    expect(screen.getByText("What is Tokyo?")).toBeInTheDocument();
  });

  it("calls onNewChat when the new chat button is clicked", async () => {
    const user = userEvent.setup();
    const onNewChat = vi.fn();
    render(
      <Sidebar
        open={true}
        conversations={conversations}
        activeConversationId="1"
        onNewChat={onNewChat}
        onSelectConversation={vi.fn()}
      />,
    );

    await user.click(screen.getByRole("button", { name: "+ New chat" }));

    expect(onNewChat).toHaveBeenCalledOnce();
  });

  it("calls onSelectConversation with the clicked conversation's id", async () => {
    const user = userEvent.setup();
    const onSelectConversation = vi.fn();
    render(
      <Sidebar
        open={true}
        conversations={conversations}
        activeConversationId="1"
        onNewChat={vi.fn()}
        onSelectConversation={onSelectConversation}
      />,
    );

    await user.click(screen.getByText("What is Berlin?"));

    expect(onSelectConversation).toHaveBeenCalledWith("1");
  });
});
