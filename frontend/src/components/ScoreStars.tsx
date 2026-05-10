"use client";

import { Star } from "lucide-react";

interface ScoreStarsProps {
  score: number;
  size?: "sm" | "md";
}

export default function ScoreStars({ score, size = "sm" }: ScoreStarsProps) {
  const iconSize = size === "sm" ? "h-3.5 w-3.5" : "h-5 w-5";
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <Star
          key={i}
          className={`${iconSize} ${
            i <= score ? "fill-amber-400 text-amber-400" : "text-gray-300"
          }`}
        />
      ))}
    </div>
  );
}
