"use client";

import clsx from "clsx";

const STATUS_STYLES: Record<string, string> = {
  new: "bg-blue-100 text-blue-700",
  reviewed: "bg-amber-100 text-amber-700",
  hired: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
  archived: "bg-gray-100 text-gray-500",
};

interface StatusBadgeProps {
  status: string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize",
        STATUS_STYLES[status] || "bg-gray-100 text-gray-700"
      )}
    >
      {status}
    </span>
  );
}
