export interface Room {
  id: number;
  room_type: string;
  price: number;
  currency: string;
  availability_count: number;
}

export interface Hotel {
  id: number;
  name: string;
  city_slug: string;
  address: string;
  description: string;
  star_rating: number;
  rooms: Room[];
  amenities: string[];
  images: string[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  hotels?: Hotel[];
}

export interface Conversation {
  id: string;
  title: string;
}

export const WELCOME_MESSAGE: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content: "Hi! I'm your travel assistant. Ask me about a city.",
};
