import { useState } from "react";

/*
  Small hover/focus tooltip component used to explain
  why recommendation-related fields are needed.
*/
export default function InfoTooltip({ text }) {
    const [open, setOpen] = useState(false);

    return (
        <span
            className="relative inline-flex items-center"
            onMouseEnter={() => setOpen(true)}
            onMouseLeave={() => setOpen(false)}
            onFocus={() => setOpen(true)}
            onBlur={() => setOpen(false)}
            tabIndex={0}
        >
      {/* Small info icon */}
            <span className="ml-2 inline-flex h-5 w-5 cursor-help items-center justify-center rounded-full bg-slate-200 text-xs font-bold text-slate-700">
        i
      </span>

            {/* Tooltip content */}
            {open && (
                <span className="absolute left-1/2 top-full z-20 mt-2 w-64 -translate-x-1/2 rounded-xl border border-slate-200 bg-white p-3 text-xs leading-5 text-slate-700 shadow-soft">
          {text}
        </span>
            )}
    </span>
    );
}
