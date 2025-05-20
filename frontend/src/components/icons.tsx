import { AlertTriangle, CheckCircle2, LucideProps } from "lucide-react"

export type IconProps = LucideProps

export const Icons = {
  spinner: (props: IconProps) => (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  ),
  error: AlertTriangle,
  success: CheckCircle2,
  amazonAds: (props: IconProps) => (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <path
        d="M18.42 13.75C17.5 13.75 16.75 14.5 16.75 15.42C16.75 16.33 17.5 17.08 18.42 17.08C19.33 17.08 20.08 16.33 20.08 15.42C20.08 14.5 19.33 13.75 18.42 13.75Z"
        fill="currentColor"
      />
      <path
        d="M6.25 13.75C5.33 13.75 4.58 14.5 4.58 15.42C4.58 16.33 5.33 17.08 6.25 17.08C7.17 17.08 7.92 16.33 7.92 15.42C7.92 14.5 7.17 13.75 6.25 13.75Z"
        fill="currentColor"
      />
      <path
        d="M18.33 7C17.35 7 16.5 7.67 16.28 8.58L8.39 6.95C8.09 6.05 7.24 5.42 6.25 5.42C5.02 5.42 4 6.43 4 7.67C4 8.9 5.02 9.92 6.25 9.92C7.09 9.92 7.84 9.46 8.24 8.77L16.03 10.36C16.03 10.39 16.03 10.41 16.03 10.44C16.03 11.68 17.05 12.69 18.28 12.69C19.52 12.69 20.53 11.68 20.53 10.44C20.53 9.21 19.52 8.19 18.28 8.19C18.29 8.19 18.32 7 18.33 7Z"
        fill="currentColor"
      />
    </svg>
  ),
} 