import os
import secrets
import subprocess

from arrow.celery import app
from .models import Submission, SubmissionTestResult, SubmissionTestGroupResult


def create_and_write_to_file_binary(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        f = open(path, 'wb')
        f.write(data)
        f.close()
    except IOError:
        return Exception(f'FAILED TO WRITE/OPEN FILE: {path}')


def create_and_write_to_file(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        f = open(path, 'w')
        f.write(data)
        f.close()
    except IOError:
        return Exception(f'FAILED TO WRITE/OPEN FILE: {path}')


def cpp17_submission_compilation(app_path, folder, submission):
    create_and_write_to_file(f'{app_path}{folder}/submission.cpp',
                             submission.data)
    try:
        cp = subprocess.run(
            f'/bin/su -c "g++ -std=c++17 -static -lm -s -x c++ -W -O2 -std=c++17 -o usercode/submission submission.cpp" dummy',
            shell=True, capture_output=True, cwd=f'{app_path}{folder}',
            timeout=10)  # if too long then its bad
    except subprocess.TimeoutExpired:
        submission.testing = False
        submission.tested = True
        submission.verdict = Submission.CP
        submission.verdict_message = 'Compilation Error'
        submission.verdict_description = 'Compilation took too long'
        submission.save()
        return Submission.CP

    if cp.returncode != 0:
        submission.testing = False
        submission.tested = True
        submission.verdict = Submission.CP
        submission.verdict_message = 'Compilation Error'
        submission.verdict_description = cp.stdout.decode() + '\n' + cp.stderr.decode()
        submission.save()
        return Submission.CP


def python3_submission_compilation(app_path, folder, submission):
    create_and_write_to_file(f'{app_path}{folder}/usercode/submission.py',
                             submission.data)


compilation_dict = {
    Submission.CPP17: cpp17_submission_compilation,
    Submission.PYTHON3: python3_submission_compilation
}

run_command_dict = {
    Submission.CPP17: './submission',
    Submission.PYTHON3: '/usr/bin/python3.7 submission.py'
}


def set_test_error(submission, test_result=None, message='Test Error',
                   debug_message='',
                   debug_description=''):
    submission.testing = False
    submission.tested = True
    submission.verdict = Submission.TE
    submission.verdict_message = message
    submission.verdict_debug_message = debug_message
    submission.verdict_debug_description = debug_description

    if test_result is not None:
        test_result.verdict = Submission.TE
        test_result.verdict_message = message
        test_result.verdict_debug_message = debug_message
        test_result.verdict_debug_description = debug_description


def copy_payload_and_compile_all(submission, tests, app_path, folder):
    # --------------------------------------------------------------------------
    # Copy payload folder at /app/polygon/payload
    cp = subprocess.run(
        f'mkdir {app_path}{folder} && cp -rp {app_path}payload/* {app_path}{folder}',
        shell=True)
    if cp.returncode != 0:
        set_test_error(submission, debug_message='Copy payload failed')
        raise Exception('Copy payload failed')

    # Copy user code and compile it
    if compilation_dict[submission.submission_type](app_path, folder,
                                                    submission) == Submission.CP:
        return Submission.CP
    print('User code compiled')
    # ==========================================================================

    # --------------------------------------------------------------------------
    # Copy solution checker and compile if needed
    if submission.problem.solution_compiled is not None:
        print('Solution does not need compilation.')
        create_and_write_to_file_binary(f'{app_path}{folder}/solution',
                                        submission.problem.solution_compiled)
        subprocess.run(f'chmod +x {app_path}{folder}/solution', shell=True)
    else:
        create_and_write_to_file(f'{app_path}{folder}/solution.cpp',
                                 submission.problem.solution)
        cp = subprocess.run(
            f'g++ -std=c++17 -static -o {app_path}{folder}/solution {app_path}{folder}/solution.cpp',
            shell=True, capture_output=True)
        if cp.returncode != 0:
            set_test_error(submission,
                           debug_message='Solution compilation error',
                           debug_description=cp.stdout.decode() + '\n' + cp.stderr.decode())
            submission.save()
            raise Exception('Solution compilation error')
        try:
            fs = open(f'{app_path}{folder}/solution', 'rb')
            problem = submission.problem
            problem.solution_compiled = fs.read()
            problem.save()
            fs.close()
        except IOError:
            print('FAILED TO READ FILE: compiled solution')
    print('solution compiled')

    if submission.problem.checker_compiled is not None:
        print('Checker does not need compilation.')
        create_and_write_to_file_binary(f'{app_path}{folder}/checker',
                                        submission.problem.checker_compiled)
        subprocess.run(f'chmod +x {app_path}{folder}/checker', shell=True)
    else:
        create_and_write_to_file(f'{app_path}{folder}/checker.cpp',
                                 submission.problem.checker)
        cp = subprocess.run(
            f'g++ -std=c++17 -static -o {app_path}{folder}/checker {app_path}{folder}/checker.cpp',
            shell=True, capture_output=True)
        if cp.returncode != 0:
            set_test_error(submission,
                           debug_message='Checker compilation error',
                           debug_description=cp.stdout.decode() + '\n' + cp.stderr.decode())
            submission.save()
            raise Exception('Checker compilation error')
        try:
            fs = open(f'{app_path}{folder}/checker', 'rb')
            problem = submission.problem
            problem.checker_compiled = fs.read()
            problem.save()
            fs.close()
        except IOError:
            print('FAILED TO READ FILE: compiled checker')
    print('checker compiled')
    # ==========================================================================

    # --------------------------------------------------------------------------
    # if problem is interactive then compile interactor.
    if submission.problem.is_interactive:
        if submission.problem.interactor_compiled is not None:
            print('Interactor does not need compilation.')
            create_and_write_to_file_binary(f'{app_path}{folder}/interactor',
                                            submission.problem.interactor_compiled)
            subprocess.run(f'chmod +x {app_path}{folder}/interactor',
                           shell=True)
        else:
            create_and_write_to_file(f'{app_path}{folder}/interactor.cpp',
                                     submission.problem.interactor)
            cp = subprocess.run(
                f'g++ -std=c++17 -static -o {app_path}{folder}/interactor {app_path}{folder}/interactor.cpp',
                shell=True, capture_output=True)
            if cp.returncode != 0:
                set_test_error(submission,
                               debug_message='Interactor compilation error',
                               debug_description=cp.stdout.decode() + '\n' + cp.stderr.decode())
                submission.save()
                raise Exception('interactor compilation error')
            try:
                fs = open(f'{app_path}{folder}/interactor', 'rb')
                problem = submission.problem
                problem.interactor_compiled = fs.read()
                problem.save()
                fs.close()
            except IOError:
                print('FAILED TO READ FILE: compiled interactor')
        print('interactor compiled')
    # ==========================================================================

    # --------------------------------------------------------------------------
    # Copy and compile generators
    for generator in submission.problem.generator_set.all():
        if generator.generator_compiled is not None:
            print(f'Generator {generator.name} does not need compilation.')
            create_and_write_to_file_binary(
                f'{app_path}{folder}/{generator.name}',
                generator.generator_compiled)
            subprocess.run(f'chmod +x {app_path}{folder}/{generator.name}',
                           shell=True)
        else:
            create_and_write_to_file(f'{app_path}{folder}/{generator.name}.cpp',
                                     generator.generator)
            cp = subprocess.run(
                f'g++ -std=c++17 -static -o {app_path}{folder}/{generator.name} {app_path}{folder}/{generator.name}.cpp',
                shell=True, capture_output=True)
            if cp.returncode != 0:
                set_test_error(submission,
                               debug_message='Generator compilation error',
                               debug_description=cp.stdout.decode() + '\n' + cp.stderr.decode())
                submission.save()
                raise Exception(f'Generator: {generator} compilation error')
            try:
                fs = open(f'{app_path}{folder}/{generator.name}', 'rb')
                generator.generator_compiled = fs.read()
                generator.save()
                fs.close()
            except IOError:
                print(
                    f'FAILED TO READ FILE: compiled generator {generator.name}')
        print(f'Generator: {generator.name} compiled')
    # ==========================================================================


def generate_test(submission, test, test_result, app_path, folder):
    if test.use_generator:
        # Run generator
        cp = subprocess.run(
            f'{app_path}{folder}/{test.generator.name} {test.data} | tee {app_path}{folder}/input_file' +
            (
                f' {app_path}{folder}/usercode/input_file' if not submission.problem.is_interactive else ''),
            shell=True, capture_output=True)
        if cp.returncode != 0:
            test_result.verdict = SubmissionTestResult.TE
            test_result.verdict_debug_message = f'Generator exit code {cp.returncode}'
            test_result.save()
            raise Exception(
                f'Generator: {test.generator} runtime error\n Generator output: \n{cp.stdout.decode()}\n{cp.stderr.decode()}')
    else:
        # Copy test
        create_and_write_to_file(f'{app_path}{folder}/input_file',
                                 test.data)
        if not submission.problem.is_interactive:
            create_and_write_to_file(
                f'{app_path}{folder}/usercode/input_file',
                test.data)
    print(f'Test #{test.index} writen')


def parse_isolate_meta_file(path):
    # Parse meta file
    try:
        fs = open(path)
        raw_meta = fs.read()
        fs.close()
    except IOError:
        # Wasp pretty common in past.
        print('FAILED TO READ/OPEN FILE: meta. sandbox failed')
        raise Exception(
            'FAILED TO READ/OPEN FILE: meta. sandbox failed')
    meta = dict()
    print(raw_meta)
    for i in raw_meta.split('\n'):
        if i != '':
            meta[i[0:i.find(':')]] = i[i.find(':') + 1:]
    return meta


# prepare some constants
# TODO make them adjustable
container_wall_time_limit = 300  # 300 seconds for whole task
wall_time_limit = 10  # 10 seconds


def execute_submission(submission, test_result, app_path, folder):
    memory_limit = submission.problem.memory_limit
    time_limit = submission.problem.time_limit
    run_command = f'{app_path}{folder}/run_isolate.sh {app_path}{folder} {str(memory_limit)} {str(time_limit)} {wall_time_limit} {run_command_dict[submission.submission_type]}'
    try:
        cp = subprocess.run(f'sh {run_command}',
                            timeout=container_wall_time_limit,
                            capture_output=True,
                            cwd=f'{app_path}{folder}',
                            shell=True)
        test_result.verdict_debug_message += '\n' + cp.stdout.decode() + '\n\n' + cp.stderr.decode()
        test_result.save()
    except subprocess.TimeoutExpired:
        test_result.verdict = SubmissionTestResult.WTL
        test_result.save()
        return False
    return True


def execute_submission_interactive(submission, test_result, app_path, folder):
    memory_limit = submission.problem.memory_limit
    time_limit = submission.problem.time_limit
    run_command = f'{app_path}{folder}/run_isolate_interactive.sh {app_path}{folder} {str(memory_limit)} {str(time_limit)} {wall_time_limit} {run_command_dict[submission.submission_type]}'
    interactor_command = f'{app_path}{folder}/interactor {app_path}{folder}/input_file {app_path}{folder}/output_file'
    try:
        # We executing solo with out sh script. It is easier that way.
        subprocess.run(f'mkfifo {app_path}{folder}/fifo',
                       cwd=f'{app_path}{folder}', shell=True)
        subprocess.run(f'isolate --cg --init',
                       cwd=f'{app_path}{folder}', shell=True)
        cp = subprocess.run(
            f'{interactor_command} < {app_path}{folder}/fifo | sh {run_command} > {app_path}{folder}/fifo ' + '; exit "${PIPESTATUS[0]}"',
            executable='/bin/bash',
            timeout=container_wall_time_limit,
            capture_output=True,
            cwd=f'{app_path}{folder}',
            shell=True)
    except subprocess.TimeoutExpired:
        test_result.verdict = Submission.WTL
        test_result.verdict_message = 'Wall time limit exceeded'
        test_result.save()
        return False
    return True


def check_isolate_failed(submission, test_result, meta):
    if 'status' in meta and meta['status'] == 'XX':
        set_test_error(submission,
                       test_result,
                       debug_message='Meta status is XX')
        test_result.save()
        submission.save()
        raise Exception('Meta status is XX retrying...')


def apply_meta_related_verdicts(meta, test, test_result):
    # Check non checker related verdicts
    meta_status = {
        'RE': Submission.RE,
        'TO': Submission.TLE,
        'SG': Submission.MLE,
        'XX': Submission.TE,
    }

    meta_status_verbose = {
        'RE': 'Runtime error',
        'TO': 'Time limit exceeded',
        'SG': 'Memory limit exceeded',
        'XX': 'Test error',
    }

    if 'status' in meta:
        if meta['status'] in meta_status:
            test_result.verdict = meta_status[meta['status']]
            test_result.verdict_message = \
                f'{meta_status_verbose[meta["status"]]} on test #{test.index}'
            test_result.save()
            return False
    return True


def execute_judge_solution(submission, test_result, app_path, folder):
    if not submission.problem.is_interactive:
        cp = subprocess.run(
            f'{app_path}{folder}/solution < {app_path}{folder}/input_file > {app_path}{folder}/answer_file',
            shell=True)
        if cp.returncode != 0:
            test_result.verdict = SubmissionTestResult.TF
            test_result.verdict_debug_message = f'Judge Solution exit code {cp.returncode}'
            test_result.save()
            return False
    else:
        # make pipe for interactor
        subprocess.run(f'mkfifo {app_path}{folder}/fifo',
                       cwd=f'{app_path}{folder}', shell=True)
        interactor_command = f'{app_path}{folder}/interactor {app_path}{folder}/input_file {app_path}{folder}/answer_file'
        cp = subprocess.run(
            f'{interactor_command} < {app_path}{folder}/fifo | {app_path}{folder}/solution > {app_path}{folder}/fifo ' + '; exit "${PIPESTATUS[0]}"',
            # f'{app_path}{folder}/solution < {app_path}{folder}/input_file > {app_path}{folder}/answer_file',
            executable='/bin/bash',
            cwd=f'{app_path}{folder}',
            shell=True)
        # rm pipe
        cp = subprocess.run(f'rm {app_path}{folder}/fifo',
                            cwd=f'{app_path}{folder}', shell=True)
        if cp.returncode != 0:
            test_result.verdict = SubmissionTestResult.TF
            test_result.verdict_debug_message = f'Judge Solution exit code {cp.returncode}'
            test_result.save()
            return False
    return True


def apply_checker_verdict(submission, test, test_result, checker_returncode):
    # Get checker verdict
    checker_verdict_dict = {
        0: Submission.OK,
        1: Submission.WA,
        2: Submission.PE,
        3: Submission.TF,
    }
    checker_verdict_dict_verbose = {
        0: 'Accepted',
        1: 'Wrong answer',
        2: 'Presentation error',
        3: 'Test Fail',
    }

    if checker_returncode != 0:
        if checker_returncode == 7:  # if solution is graded
            if not submission.problem.is_graded or (
                    submission.problem.is_graded and submission.problem.is_sub_task):
                test_result.verdict = Submission.TF
                test_result.verdict_message += '\nTest Failed'
                test_result.verdict_debug_message = 'Checker error'
                test_result.verdict_debug_description = 'Checker is a grader but problem is not graded or you mixed is_graded and is_sub_task!'
                test_result.save()
                return False
        if checker_returncode in checker_verdict_dict:
            test_result.verdict = checker_verdict_dict[checker_returncode]
            test_result.verdict_message += f'\n{checker_verdict_dict_verbose[checker_returncode]} on test #{test.index}'
            test_result.save()
            return False
        else:
            test_result.verdict = Submission.UNKNOWN_CODE
            test_result.verdict_message = f'{checker_verdict_dict_verbose[checker_returncode]} on test #{test.index}'
            test_result.save()
            return False
    test_result.verdict = SubmissionTestResult.OK
    test_result.verdict_message = 'Accepted'
    test_result.save()
    return True


def execute_checker(submission, test_result, app_path, folder):
    run_command = f'{app_path}{folder}/checker {app_path}{folder}/input_file {app_path}{folder}/usercode/output_file {app_path}{folder}/answer_file {app_path}{folder}/checker_result'
    if submission.problem.is_interactive:
        run_command = f'{app_path}{folder}/checker {app_path}{folder}/input_file {app_path}{folder}/output_file {app_path}{folder}/answer_file {app_path}{folder}/checker_result'
    cp = subprocess.run(run_command, shell=True, capture_output=True,
                        cwd=f'{app_path}{folder}', )
    checker_returncode = cp.returncode
    checker_output = cp.stdout.decode() + '\n' + cp.stderr.decode()
    try:
        fs = open(f'{app_path}{folder}/checker_result')
        test_result.verdict_debug_description += '\n' + fs.read(2024)
        test_result.save()
    except IOError:
        print(f'FAILED to read checker_result, Please check checker')
        # test_result.verdict = SubmissionTestResult.TF
        # test_result.verdict_message = 'FAILED to read: checker_result. Please check checker'
    print(checker_output)
    return checker_returncode, checker_output


def run_judge_sandbox(submission, tests, app_path, folder):
    # --------------------------------------------------------------------------
    # Delete previous records
    submission.submissiontestresult_set.all().delete()
    # ==========================================================================

    if copy_payload_and_compile_all(submission, tests, app_path,
                                    folder) == Submission.CP:
        return Submission.CP

    # --------------------------------------------------------------------------
    # ensure dir permission is ok
    subprocess.run(f'chmod -R 777 {app_path}{folder}', shell=True)
    subprocess.run(f'chmod -R 677 {app_path}{folder}/usercode', shell=True)
    subprocess.run(f'chmod 677 {app_path}{folder}/usercode', shell=True)
    print('Files copied and compiled')
    # ==========================================================================

    # --------------------------------------------------------------------------
    # Ok, all sources compiled. Now we should test submission
    # We will create and write each submission verdict to model.
    # Currently we don't save user output.
    max_time_used = -1
    max_memory_used = -1
    test_results = []
    for test in tests:
        test_result = SubmissionTestResult(
            submission=submission,
            test=test,
        )
        test_result.save()
        test_results.append(test_result)
        # Notify user about test
        submission.testing_message = f'Testing on test #{test.index}'
        submission.save()

        # Prepare test input
        try:
            generate_test(submission, test, test_result, app_path, folder)
        except Exception as e:
            print(e)
            break
        # ==========================================================================

        # clean up an isolate
        # TODO replace isolate with proper sandboxing solution
        subprocess.run(f'isolate --cleanup --cg', shell=True)
        # ==========================================================================

        # Run user code
        if not submission.problem.is_interactive:
            if not execute_submission(submission,
                                      test_result,
                                      app_path,
                                      folder):
                break
        else:
            if not execute_submission_interactive(submission,
                                                  test_result,
                                                  app_path,
                                                  folder):
                break
            meta = parse_isolate_meta_file(f'{app_path}{folder}/meta')
            # If isolate fails => retry
            check_isolate_failed(submission, test_result, meta)

            test_result.verdict_debug_message += '\ninteractor\n'
            # rm pipe due to user ability to skip some inputs and
            # they will occur in next test, we do not want that.
            cp = subprocess.run(f'rm {app_path}{folder}/fifo',
                                cwd=f'{app_path}{folder}', shell=True)
            return_code = cp.returncode
            if return_code != 0:
                if cp.returncode == 3:
                    test_result.verdict = Submission.TF
                    test_result.verdict_message = 'Test Failed'
                    test_result.verdict_debug_message = 'Interactor error'
                    test_result.save()
                    break
                checker_verdict_dict = {
                    1: SubmissionTestResult.WA,
                    2: SubmissionTestResult.PE,
                    3: SubmissionTestResult.TF,
                }
                checker_verdict_dict_verbose = {
                    1: 'Wrong answer',
                    2: 'Presentation error',
                    3: 'Test Fail',
                }
                print(
                    f'Interactor on test #{test.index} return code: {return_code}. stdout: \n{cp.stdout.decode()}\n stderr:\n{cp.stderr.decode()}')
                if return_code in checker_verdict_dict:
                    test_result.verdict = checker_verdict_dict[return_code]
                    test_result.verdict_message = f'{checker_verdict_dict_verbose[return_code]} on test #{test.index}'
                    test_result.save()
                    break
                else:
                    test_result.verdict = Submission.UNKNOWN_CODE
                    test_result.verdict_debug_message = f'Interactor exited with {return_code} on test #{test.index}'
                    test_result.save()
                    break
        print(f'Successful execution')
        # ==========================================================================

        # Parse meta file
        meta = parse_isolate_meta_file(f'{app_path}{folder}/meta')
        # ==========================================================================

        # If isolate fails => retry
        check_isolate_failed(submission, test_result, meta)
        # ==========================================================================

        # Lets tell user how bad he is.
        if 'time' in meta:
            test_result.time_used = float(meta['time'])
            max_time_used = max(max_time_used, float(meta['time']))
            submission.max_time_used = max_time_used
        if 'max-rss' in meta:
            test_result.memory_used = int(meta['max-rss'])
            max_memory_used = max(max_memory_used, int(meta['max-rss']))
            submission.max_memory_used = max_memory_used
        # ==========================================================================

        # Check non checker related verdicts
        if not apply_meta_related_verdicts(meta, test, test_result):
            break
        # ==========================================================================

        # OK now lets check result
        # First run solution
        if not execute_judge_solution(submission, test_result, app_path,
                                      folder):
            break
        print('Solution executed')
        # ==========================================================================

        # Now lets run checker
        # ./checker usercode/input_file usercode/output_file answer_file
        # Checker should write result to fourth argument (checker_result)
        checker_returncode, checker_output = execute_checker(submission,
                                                             test_result,
                                                             app_path,
                                                             folder)
        # for debug
        if checker_returncode == 3:
            test_result.verdict = Submission.TF
            test_result.verdict_message += '\nTest Failed'
            test_result.verdict_debug_message = 'Checker error'
            test_result.verdict_debug_description = checker_output
            test_result.save()
            break
        print(f'Checker executed')
        # ==========================================================================

        # Get checker verdict
        print(f'Checker result: {checker_returncode}')
        if not apply_checker_verdict(submission, test, test_result, checker_returncode):
            break
    submission.verdict = test_results[-1].verdict
    submission.verdict_message = test_results[-1].verdict_message
    submission.testing = False
    submission.tested = True
    submission.save()
    subprocess.run(f'rm -rf {app_path}{folder}', shell=True)
    return Submission.OK


def run_judge_sandbox_sub_task_problem(submission, tests, app_path, folder):
    # --------------------------------------------------------------------------
    # Delete previous records
    submission.submissiontestresult_set.all().delete()
    submission.submissiontestgroupresult_set.all().delete()
    # ==========================================================================

    if copy_payload_and_compile_all(submission, tests, app_path,
                                    folder) == Submission.CP:
        return Submission.CP

    # --------------------------------------------------------------------------
    # ensure dir permission is ok
    subprocess.run(f'chmod -R 777 {app_path}{folder}', shell=True)
    subprocess.run(f'chmod -R 677 {app_path}{folder}/usercode', shell=True)
    subprocess.run(f'chmod 677 {app_path}{folder}/usercode', shell=True)
    print('Files copied and compiled')
    # ==========================================================================

    # --------------------------------------------------------------------------
    # Ok, all sources compiled. Now we should test submission
    # We will create and write each submission verdict to model.
    # Currently we don't save user output.
    max_time_used = -1
    max_memory_used = -1
    test_results = []
    for test in tests:
        test_result = SubmissionTestResult(
            submission=submission,
            test=test,
        )
        test_result.save()
        test_results.append(test_result)
        # Notify user about test
        submission.testing_message = f'Testing on test #{test.index}'
        submission.save()

        # Prepare test input
        try:
            generate_test(submission, test, test_result, app_path, folder)
        except Exception as e:
            print(e)
            continue
        # ==========================================================================

        # clean up an isolate
        # TODO replace isolate with proper sandboxing solution
        subprocess.run(f'isolate --cleanup --cg', shell=True)
        # ==========================================================================

        # Run user code
        if not submission.problem.is_interactive:
            if not execute_submission(submission,
                                      test_result,
                                      app_path,
                                      folder):
                continue
        else:
            if not execute_submission_interactive(submission,
                                                  test_result,
                                                  app_path,
                                                  folder):
                continue
            meta = parse_isolate_meta_file(f'{app_path}{folder}/meta')
            # If isolate fails => retry
            check_isolate_failed(submission, test_result, meta)

            test_result.verdict_debug_message += '\ninteractor\n'
            # rm pipe due to user ability to skip some inputs and
            # they will occur in next test, we do not want that.
            cp = subprocess.run(f'rm {app_path}{folder}/fifo',
                                cwd=f'{app_path}{folder}', shell=True)
            return_code = cp.returncode
            if return_code != 0:
                if cp.returncode == 3:
                    test_result.verdict = Submission.TF
                    test_result.verdict_message = 'Test Failed'
                    test_result.verdict_debug_message = 'Interactor error'
                    test_result.save()
                    continue
                checker_verdict_dict = {
                    1: SubmissionTestResult.WA,
                    2: SubmissionTestResult.PE,
                    3: SubmissionTestResult.TF,
                }
                checker_verdict_dict_verbose = {
                    1: 'Wrong answer',
                    2: 'Presentation error',
                    3: 'Test Fail',
                }
                print(
                    f'Interactor on test #{test.index} return code: {return_code}. stdout: \n{cp.stdout.decode()}\n stderr:\n{cp.stderr.decode()}')
                if return_code in checker_verdict_dict:
                    test_result.verdict = checker_verdict_dict[return_code]
                    test_result.verdict_message = f'{checker_verdict_dict_verbose[return_code]} on test #{test.index}'
                    test_result.save()
                    continue
                else:
                    test_result.verdict = Submission.UNKNOWN_CODE
                    test_result.verdict_debug_message = f'Interactor exited with {return_code} on test #{test.index}'
                    test_result.save()
                    continue
        print(f'Successful execution')
        # ==========================================================================

        # Parse meta file
        meta = parse_isolate_meta_file(f'{app_path}{folder}/meta')
        # ==========================================================================

        # If isolate fails => retry
        check_isolate_failed(submission, test_result, meta)
        # ==========================================================================

        # Lets tell user how bad he is.
        if 'time' in meta:
            test_result.time_used = float(meta['time'])
            max_time_used = max(max_time_used, float(meta['time']))
            submission.max_time_used = max_time_used
        if 'max-rss' in meta:
            test_result.memory_used = int(meta['max-rss'])
            max_memory_used = max(max_memory_used, int(meta['max-rss']))
            submission.max_memory_used = max_memory_used
        # ==========================================================================

        # Check non checker related verdicts
        if not apply_meta_related_verdicts(meta, test, test_result):
            continue
        # ==========================================================================

        # OK now lets check result
        # First run solution
        if not execute_judge_solution(submission, test_result, app_path,
                                      folder):
            continue
        print('Solution executed')
        # ==========================================================================

        # Now lets run checker
        # ./checker usercode/input_file usercode/output_file answer_file
        # Checker should write result to fourth argument (checker_result)
        checker_returncode, checker_output = execute_checker(submission,
                                                             test_result,
                                                             app_path,
                                                             folder)
        # for debug
        if checker_returncode == 3:
            test_result.verdict = Submission.TF
            test_result.verdict_message += '\nTest Failed'
            test_result.verdict_debug_message = 'Checker error'
            test_result.verdict_debug_description = checker_output
            test_result.save()
            continue
        print(f'Checker executed')
        # ==========================================================================

        # Get checker verdict
        apply_checker_verdict(submission, test, test_result, checker_returncode)
        print(f'Checker result: {checker_returncode}')

    # Now lets count points
    net_points = 0
    # Not necessary for sub task problem
    # for test_result in test_results:
    #     test_result.points = test_result.test.points
    #     net_points += test_result.test.points
    ok_tests = set(
        map(lambda tr: tr.test.pk,
            filter(lambda tr: tr.verdict == SubmissionTestResult.OK,
                   test_results)
            )
    )
    test_group_results = dict()
    for test_group in submission.problem.testgroup_set.all():
        test_group_result = SubmissionTestGroupResult(submission=submission,
                                                      problem=submission.problem,
                                                      test_group=test_group
                                                      )
        required_tests = set(test_group.test_set.values_list('pk', flat=True))
        if required_tests.issubset(ok_tests):
            test_group_result.points = test_group.points
            net_points += test_group.points
        test_group_results[test_group.name] = test_group_results
        test_group_result.save()
    for test_result in test_results:
        try:
            if test_result.test_group_result:
                test_result.test_group_result = test_group_results[
                    test_result.test.group.name]
                test_result.save()
        except Exception as e:
            print(e)

    submission.verdict = Submission.OK
    submission.verdict_message = f'OK. Points: {net_points}'
    submission.testing = False
    submission.tested = True
    submission.points = net_points
    submission.save()

    subprocess.run(f'rm -rf {app_path}{folder}', shell=True)
    return Submission.OK


def prepare_sandbox_folder():
    app_path = os.path.dirname(os.path.realpath(__file__)) + '/'
    folder = 'temp/' + secrets.token_hex(16)

    return app_path, folder


@app.task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 3},
          default_retry_delay=10)
def judge_submission_task(submission_id):
    submission = Submission.objects.get(pk=submission_id)
    submission.erase_verdict()
    submission.tested = False
    submission.testing = True
    submission.save()

    tests = submission.problem.test_set.order_by('index')

    app_path, folder = prepare_sandbox_folder()

    if submission.problem.is_sub_task:
        try:
            return run_judge_sandbox_sub_task_problem(submission, tests,
                                                      app_path, folder)
        except Exception as e:
            subprocess.run(f'rm -rf {app_path}{folder}', shell=True)
            submission.testing = False
            submission.tested = True
            submission.verdict = Submission.TE
            submission.verdict_message = 'Test Error'
            submission.save()
            raise e
    if submission.problem.is_graded:
        pass
    elif submission.submission_type in [Submission.CPP17, Submission.PYTHON3]:
        try:
            return run_judge_sandbox(submission, tests, app_path, folder)
        except Exception as e:
            subprocess.run(f'rm -rf {app_path}{folder}', shell=True)
            submission.testing = False
            submission.tested = True
            submission.verdict = Submission.TE
            submission.verdict_message = 'Test Error'
            submission.save()
            raise e
    # we don't wont any collision
    subprocess.run(f'rm -rf {app_path}{folder}', shell=True)
    return


@app.task
def sandbox_run_on_error(request, exc, traceback,
                         submission_id):
    print('Task {0!r} raised error: {1!r}'.format(request.id, exc))
    submission = Submission.objects.get(pk=submission_id)
    if submission:
        submission.testing = False
        submission.tested = True
        submission.verdict = submission.TE
        submission.verdict_message = f'Test failed, notify admin'
        submission.verdict_debug_description = str(traceback)
        submission.save()
