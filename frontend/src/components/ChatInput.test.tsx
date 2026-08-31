import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatInput } from "./ChatInput";

describe("ChatInput", () => {
  it("submits the trimmed message and clears the input on Enter", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatInput disabled={false} onSend={onSend} />);

    const textarea = screen.getByPlaceholderText("Ask about a city...");
    await user.type(textarea, "what is berlin?");
    await user.keyboard("{Enter}");

    expect(onSend).toHaveBeenCalledWith("what is berlin?");
    expect(textarea).toHaveValue("");
  });

  it("does not submit on Shift+Enter, inserts a newline instead", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatInput disabled={false} onSend={onSend} />);

    const textarea = screen.getByPlaceholderText("Ask about a city...");
    await user.type(textarea, "line one");
    await user.keyboard("{Shift>}{Enter}{/Shift}");
    await user.type(textarea, "line two");

    expect(onSend).not.toHaveBeenCalled();
    expect(textarea).toHaveValue("line one\nline two");
  });

  it("does not submit an empty or whitespace-only message", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatInput disabled={false} onSend={onSend} />);

    const textarea = screen.getByPlaceholderText("Ask about a city...");
    await user.type(textarea, "   ");
    await user.keyboard("{Enter}");

    expect(onSend).not.toHaveBeenCalled();
  });

  it("disables the textarea and send button when disabled", () => {
    render(<ChatInput disabled={true} onSend={vi.fn()} />);

    expect(screen.getByPlaceholderText("Ask about a city...")).toBeDisabled();
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("disables the send button while the input is empty", () => {
    render(<ChatInput disabled={false} onSend={vi.fn()} />);

    expect(screen.getByRole("button")).toBeDisabled();
  });
});
