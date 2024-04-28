import React from "react";
import { classNames } from "@/libs/class-names";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { a11yDark as style } from "react-syntax-highlighter/dist/cjs/styles/prism";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import "katex/dist/katex.min.css"; // `rehype-katex` does not import the CSS for you;
import ReactMarkdown from "react-markdown";
// import CodeSection from "@/components/code-section";

interface MessageProps {
  role?: "system" | "user" | "assistant";
  content?: string;
  error?: string;
  partial?: boolean;
  nTokens?: number;
  richContent?: boolean;
}

function Message({
  role = "assistant",
  content = "",
  richContent = true,
  error,
  partial = false,
  nTokens,
}: MessageProps): JSX.Element {

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(content);
    } catch (error) {
      console.error('Failed to copy content: ', error);
    }
  };

  return (
    <div className="relative group"> {/* Container for hover effect and positioning */}
      <div
        className={classNames(
          "rounded-[35px] py-3 px-4 break-words font-serif overflow-x-auto shadow-md border",
          role === "user"
            // ? "bg-red-500 font-medium"
            ? "bg-red-500/[.2] font-medium"
            : role === "assistant"
            ? "bg-white ... ring-[2.5px] font-medium ring-red-400 ring-inset text-black"
            : "bg-blue-50 border-blue-200 text-white",
          partial && "shadow-md"
          
        )}
      >
        {nTokens && (
          <div className="absolute bottom-1 right-1 p-1 text-xs opacity-50 bg-gray-200 rounded font-mono">
            {nTokens}
          </div>
        )}
        <div>
          {!richContent ? (
            <div className="whitespace-pre-wrap prose prose-sm">{content}</div>
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkMath, remarkGfm]}
              rehypePlugins={[rehypeKatex, rehypeRaw]}
              skipHtml={false}
              remarkRehypeOptions={{
                allowDangerousHtml: true,
                passThrough: ["html"],
              }}
              className="prose prose-sm max-w-none"
              unwrapDisallowed={true}
              // components={{
              //   code({ inline, className, children, ...props }) {
              //     const match = /language-(\w+)/.exec(className || "");
              //     return !inline ? (
              //       match && match[1] === "mermaid" ? (
              //         // <div className="not-prose">
              //         <CodeSection code={String(children).replace(/\n$/, "")}>
              //           <div className="flex flex-row justify-around">
              //             <code className="mermaid text-sm flex-1">
              //               {String(children).replace(/\n$/, "")}
              //             </code>
              //           </div>
              //         </CodeSection>
              //       ) : (
              //         <CodeSection code={String(children).replace(/\n$/, "")}>
              //           <SyntaxHighlighter
              //             {...props}
              //             codeTagProps={{ className: "text-xs" }}
              //             style={style}
              //             language={match?.[1] || "text"}
              //             // PreTag="div"
              //             showInlineLineNumbers={true}
              //             wrapLines={true}
              //             wrapLongLines={true}
              //             showLineNumbers={false}
              //           >
              //             {String(children).replace(/\n$/, "")}
              //           </SyntaxHighlighter>
              //         </CodeSection>
              //       )
              //     ) : (
              //       // Inline code
              //       <code {...props} className={className}>
              //         {children}
              //       </code>
              //     );
              //   },
              //   pre({ children }) {
              //     return (
              //       <div className="not-prose">
              //         <pre className="text-xs">{children}</pre>
              //       </div>
              //     );
              //   },
              //   p({ children, ...props }) {
              //     return <p {...props}>{children}</p>;
              //   },
              // }}
            >
              {content + (partial ? " ▌" : "")}
            </ReactMarkdown>
          )}
        </div>
      </div>
      {role === "assistant" && (
        <button
          onClick={copyToClipboard}
          className="absolute -right-0 -bottom--0 opacity-0 mt-[-40px] mr-[30px] group-hover:opacity-100 transition-opacity duration-300 ease-in-out transform p-1 bg-transparent  hover:bg-transparent text-white rounded-full focus:outline-none"
          style={{ width: '10px', height: '10px' }}
          aria-label="Copy message to clipboard"
        >

<svg height="22px" version="1.1" viewBox="0 0 21 22" width="21px" xmlns="http://www.w3.org/2000/svg"><title/><desc/><defs/><g fill="none" fill-rule="evenodd" id="Page-1" stroke="none" stroke-width="1"><g fill="#FA5633" id="Core" transform="translate(-86.000000, -127.000000)"><g id="content-copy" transform="translate(86.500000, 127.000000)"><path d="M14,0 L2,0 C0.9,0 0,0.9 0,2 L0,16 L2,16 L2,2 L14,2 L14,0 L14,0 Z M17,4 L6,4 C4.9,4 4,4.9 4,6 L4,20 C4,21.1 4.9,22 6,22 L17,22 C18.1,22 19,21.1 19,20 L19,6 C19,4.9 18.1,4 17,4 L17,4 Z M17,20 L6,20 L6,6 L17,6 L17,20 L17,20 Z" id="Shape"/></g></g></g></svg>
        </button>
      )}
    </div>
  );
}

export default Message;


