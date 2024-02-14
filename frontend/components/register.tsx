import { Button, buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils/utils";

export function ButtonDemo() {
    return;
}


interface RegisterProps {
}

export function Register({
}: RegisterProps) {

    return (
        <div className="container relative hidden h-[800px] flex-col items-center justify-center md:grid lg:max-w-none lg:grid-cols-2 lg:px-0">
            <Button asChild
                className={cn(
                    buttonVariants({ variant: "ghost" }),
                    "absolute right-4 top-4 md:right-8 md:top-8"
                )}>
                <a href="/login">Login</a>
            </Button>
            <div>
                <div>Create an account</div>
                <Button>Register</Button>
            </div>
        </div>
    );
}